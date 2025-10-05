from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Document:
    id: str
    filename: str
    content_type: str
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectVersion:
    id: str
    created_at: datetime
    brd_markdown: str
    mermaid_diagram: str
    gap_analysis: Dict[str, List[str]]
    stakeholder_summaries: Dict[str, str]
    priority_matrix: Optional[List[Dict[str, str]]] = None


@dataclass
class Project:
    id: str
    name: str
    industry: str
    business_problem: str
    goals: str
    stakeholders: str
    timelines: str
    created_at: datetime
    updated_at: datetime
    document_ids: List[str] = field(default_factory=list)
    versions: List[ProjectVersion] = field(default_factory=list)

    def add_version(self, version: ProjectVersion) -> None:
        self.versions.insert(0, version)
        self.updated_at = version.created_at

    def add_document(self, document_id: str) -> None:
        if document_id not in self.document_ids:
            self.document_ids.append(document_id)
