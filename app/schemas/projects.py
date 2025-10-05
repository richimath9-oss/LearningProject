from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    id: UUID
    filename: str
    content_type: str
    text_preview: str = Field(description="Preview of the parsed text")
    metadata: Dict[str, str] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    documents: List[DocumentMetadata]


class ProjectCreate(BaseModel):
    name: str
    industry: str
    business_problem: str
    goals: str
    stakeholders: str
    timelines: str


class ProjectSummary(BaseModel):
    id: UUID
    name: str
    industry: str
    business_problem: str
    goals: str
    stakeholders: str
    timelines: str
    created_at: datetime
    updated_at: datetime


class VersionGapAnalysis(BaseModel):
    missing_information: List[str] = Field(default_factory=list)
    clarifying_questions: List[str] = Field(default_factory=list)


class StakeholderSummaries(BaseModel):
    executives: str
    technical_team: str
    non_technical: str


class PriorityEntry(BaseModel):
    requirement: str
    priority: str


class ProjectVersionResponse(BaseModel):
    id: UUID
    created_at: datetime
    brd_markdown: str
    mermaid_diagram: str
    gap_analysis: VersionGapAnalysis
    stakeholder_summaries: StakeholderSummaries
    priority_matrix: List[PriorityEntry] = Field(default_factory=list)


class ProjectResponse(ProjectSummary):
    document_ids: List[UUID]
    versions: List[ProjectVersionResponse]


class GenerateRequest(BaseModel):
    document_ids: List[UUID] = Field(default_factory=list)
    refresh: bool = False


class GenerateResponse(BaseModel):
    project: ProjectResponse
    version: ProjectVersionResponse


class CompareResponse(BaseModel):
    diff: str
    v1: UUID
    v2: UUID


class ExportRequest(BaseModel):
    version_id: Optional[UUID] = None
    export_format: str = Field(default="docx", regex="^(docx|pdf)$")
