import json
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.project import Document, Project, ProjectVersion


class JSONStorage:
    def __init__(self, filename: str) -> None:
        settings = get_settings()
        self._path = settings.data_dir / "storage" / filename
        if not self._path.exists():
            self._path.write_text(json.dumps({}))

    def read(self) -> Dict[str, Dict]:
        if not self._path.exists():
            return {}
        data = json.loads(self._path.read_text())
        return data

    def write(self, data: Dict[str, Dict]) -> None:
        self._path.write_text(json.dumps(data, indent=2, default=str))


class ProjectRepository:
    def __init__(self) -> None:
        self._storage = JSONStorage("projects.json")

    def _serialize_project(self, project: Project) -> Dict:
        return {
            "id": project.id,
            "name": project.name,
            "industry": project.industry,
            "business_problem": project.business_problem,
            "goals": project.goals,
            "stakeholders": project.stakeholders,
            "timelines": project.timelines,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "document_ids": project.document_ids,
            "versions": [
                {
                    "id": version.id,
                    "created_at": version.created_at.isoformat(),
                    "brd_markdown": version.brd_markdown,
                    "mermaid_diagram": version.mermaid_diagram,
                    "gap_analysis": version.gap_analysis,
                    "stakeholder_summaries": version.stakeholder_summaries,
                    "priority_matrix": version.priority_matrix,
                }
                for version in project.versions
            ],
        }

    def _deserialize_project(self, data: Dict) -> Project:
        versions = [
            ProjectVersion(
                id=version["id"],
                created_at=datetime.fromisoformat(version["created_at"]),
                brd_markdown=version["brd_markdown"],
                mermaid_diagram=version["mermaid_diagram"],
                gap_analysis=version.get("gap_analysis", {}),
                stakeholder_summaries=version.get("stakeholder_summaries", {}),
                priority_matrix=version.get("priority_matrix"),
            )
            for version in data.get("versions", [])
        ]
        project = Project(
            id=data["id"],
            name=data["name"],
            industry=data["industry"],
            business_problem=data["business_problem"],
            goals=data["goals"],
            stakeholders=data["stakeholders"],
            timelines=data["timelines"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            document_ids=data.get("document_ids", []),
            versions=versions,
        )
        return project

    def create(self, payload: Dict) -> Project:
        now = datetime.utcnow()
        project = Project(
            id=str(uuid4()),
            created_at=now,
            updated_at=now,
            document_ids=[],
            versions=[],
            **payload,
        )
        data = self._storage.read()
        data[project.id] = self._serialize_project(project)
        self._storage.write(data)
        return project

    def list(self) -> List[Project]:
        data = self._storage.read()
        return [self._deserialize_project(item) for item in data.values()]

    def get(self, project_id: str) -> Project:
        data = self._storage.read()
        project_data = data.get(project_id)
        if not project_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return self._deserialize_project(project_data)

    def update(self, project: Project) -> Project:
        data = self._storage.read()
        data[project.id] = self._serialize_project(project)
        self._storage.write(data)
        return project


class DocumentRepository:
    def __init__(self) -> None:
        self._storage = JSONStorage("documents.json")

    def _serialize(self, document: Document) -> Dict:
        return asdict(document)

    def save(self, filename: str, content_type: str, text: str, metadata: Optional[Dict[str, str]] = None) -> Document:
        document = Document(
            id=str(uuid4()),
            filename=filename,
            content_type=content_type,
            text=text,
            metadata=metadata or {},
        )
        data = self._storage.read()
        data[document.id] = self._serialize(document)
        self._storage.write(data)
        return document

    def bulk_get(self, document_ids: Iterable[str]) -> List[Document]:
        data = self._storage.read()
        documents: List[Document] = []
        for doc_id in document_ids:
            raw = data.get(str(doc_id))
            if raw:
                documents.append(Document(**raw))
        return documents

    def get(self, document_id: str) -> Document:
        data = self._storage.read()
        raw = data.get(str(document_id))
        if not raw:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return Document(**raw)


project_repository = ProjectRepository()
document_repository = DocumentRepository()
