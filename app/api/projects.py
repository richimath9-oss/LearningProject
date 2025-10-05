from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.projects import (
    CompareResponse,
    DocumentMetadata,
    ExportRequest,
    GenerateRequest,
    GenerateResponse,
    PriorityEntry,
    ProjectCreate,
    ProjectResponse,
    ProjectVersionResponse,
    UploadResponse,
)
from app.services import analysis, diff, exporter
from app.services.ai import generate_brd
from app.services.parser import parse_upload
from app.services.storage import document_repository, project_repository
from app.services.visuals import default_mermaid

router = APIRouter(prefix="/api", tags=["projects"])


def _version_to_response(version) -> ProjectVersionResponse:
    return ProjectVersionResponse(
        id=UUID(version.id),
        created_at=version.created_at,
        brd_markdown=version.brd_markdown,
        mermaid_diagram=version.mermaid_diagram,
        gap_analysis=version.gap_analysis,
        stakeholder_summaries=version.stakeholder_summaries,
        priority_matrix=[PriorityEntry(**entry) for entry in (version.priority_matrix or [])],
    )


def _project_to_response(project) -> ProjectResponse:
    return ProjectResponse(
        id=UUID(project.id),
        name=project.name,
        industry=project.industry,
        business_problem=project.business_problem,
        goals=project.goals,
        stakeholders=project.stakeholders,
        timelines=project.timelines,
        created_at=project.created_at,
        updated_at=project.updated_at,
        document_ids=[UUID(doc_id) for doc_id in project.document_ids],
        versions=[_version_to_response(version) for version in project.versions],
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile]):
    documents = []
    for file in files:
        text, metadata = parse_upload(file)
        document = document_repository.save(
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            text=text,
            metadata=metadata,
        )
        documents.append(
            DocumentMetadata(
                id=UUID(document.id),
                filename=document.filename,
                content_type=document.content_type,
                text_preview=document.text[:500],
                metadata=document.metadata,
            )
        )
    return UploadResponse(documents=documents)


@router.post("/projects", response_model=ProjectResponse)
async def create_project(payload: ProjectCreate):
    project = project_repository.create(payload.dict())
    return _project_to_response(project)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID):
    project = project_repository.get(str(project_id))
    return _project_to_response(project)


@router.post("/projects/{project_id}/generate", response_model=GenerateResponse)
async def generate_project_brd(project_id: UUID, request: GenerateRequest):
    project = project_repository.get(str(project_id))
    if request.document_ids:
        documents = document_repository.bulk_get(str(doc_id) for doc_id in request.document_ids)
    else:
        documents = document_repository.bulk_get(project.document_ids)
    references = [doc.text for doc in documents]
    payload = {
        "project_name": project.name,
        "industry": project.industry,
        "business_problem": project.business_problem,
        "goals": project.goals,
        "stakeholders": project.stakeholders,
        "timelines": project.timelines,
    }
    ai_output = generate_brd(payload, references)
    gap_analysis = analysis.build_gap_analysis(ai_output.get("brd_markdown", ""))
    priorities = analysis.prioritize_requirements(ai_output.get("brd_markdown", ""))

    from app.models.project import ProjectVersion

    mermaid_diagram = ai_output.get("mermaid_diagram") or default_mermaid(project.name)
    stakeholder_summaries = ai_output.get("stakeholder_summaries") or {
        "executives": "Strategic overview pending clarification.",
        "technical_team": "Technical deep dive to be refined after architecture review.",
        "non_technical": "User-facing summary will be refined with stakeholder input.",
    }

    version = ProjectVersion(
        id=str(uuid4()),
        created_at=datetime.utcnow(),
        brd_markdown=ai_output.get("brd_markdown", ""),
        mermaid_diagram=mermaid_diagram,
        gap_analysis=gap_analysis,
        stakeholder_summaries=stakeholder_summaries,
        priority_matrix=priorities,
    )

    project.add_version(version)
    if request.document_ids:
        for doc_id in request.document_ids:
            project.add_document(str(doc_id))
    project_repository.update(project)

    return GenerateResponse(project=_project_to_response(project), version=_version_to_response(version))


@router.get("/projects/{project_id}/compare", response_model=CompareResponse)
async def compare_versions(project_id: UUID, v1: UUID, v2: UUID):
    project = project_repository.get(str(project_id))
    version_map = {version.id: version for version in project.versions}
    version_a = version_map.get(str(v1))
    version_b = version_map.get(str(v2))
    if not version_a or not version_b:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    diff_text = diff.render_diff(version_a.brd_markdown, version_b.brd_markdown)
    return CompareResponse(diff=diff_text, v1=v1, v2=v2)


@router.post("/projects/{project_id}/export")
async def export_project(project_id: UUID, request: ExportRequest):
    project = project_repository.get(str(project_id))
    version_id = str(request.version_id) if request.version_id else None
    version = None
    if version_id:
        for candidate in project.versions:
            if candidate.id == version_id:
                version = candidate
                break
    if version is None:
        if not project.versions:
            raise HTTPException(status_code=404, detail="No versions available for export")
        version = project.versions[0]
    data, content_type = exporter.export_brd(version.brd_markdown, request.export_format)
    filename = f"{project.name.replace(' ', '_')}_BRD.{request.export_format}"
    return StreamingResponse(iter([data]), media_type=content_type, headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.post("/integrations/jira")
async def push_to_jira():
    return {"status": "stub", "message": "Jira integration not implemented in MVP."}
