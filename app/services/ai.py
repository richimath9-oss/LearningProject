from __future__ import annotations

import importlib
import textwrap
from typing import Dict, List

OpenAI = None
if importlib.util.find_spec("openai"):
    OpenAI = importlib.import_module("openai").OpenAI

from app.core.config import get_settings

MASTER_PROMPT = """You are an expert Business Analyst with 15+ years of experience in multiple industries.\nGenerate a detailed and professional Business Requirements Document (BRD) based on the provided inputs.\n\nINPUT:\n- Project Name: {project_name}\n- Industry: {industry}\n- Business Problem: {business_problem}\n- Goals: {goals}\n- Stakeholders: {stakeholders}\n- Timelines: {timelines}\n- Uploaded References: {uploaded_text_or_summary}\n\nTASKS:\n1. Create a BRD with the following sections:\n   - Executive Summary\n   - Business Objectives\n   - Scope (In Scope / Out of Scope)\n   - Functional Requirements\n   - Non-Functional Requirements\n   - Assumptions\n   - Constraints\n   - Acceptance Criteria (with Gherkin examples)\n   - Risks & Mitigation Strategies\n   - Timeline Overview\n   - Dependencies\n\n2. Adapt the tone and structure to match {industry} best practices.\n\n3. Perform a gap analysis:\n   - Flag unclear or missing requirements.\n   - Suggest clarifying questions.\n\n4. Generate a stakeholder-friendly summary for:\n   - Executives\n   - Technical teams\n   - Non-technical stakeholders\n\n5. Provide a visual requirement hierarchy in Mermaid.js format.\n\n6. Suggest potential project risks based on provided info and industry context.\n\nOUTPUT:\n- Complete BRD in structured Markdown format.\n- Separate section for summaries by stakeholder type.\n- Mermaid.js code block for visualization.\n"""


class BRDGenerationError(RuntimeError):
    """Raised when the BRD generation fails."""


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if OpenAI and self.settings.openai_api_key:
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        else:
            self._client = None

    def _format_prompt(self, payload: Dict[str, str], references: List[str]) -> str:
        merged_references = "\n\n".join(references) if references else "No reference documents provided."
        return MASTER_PROMPT.format(uploaded_text_or_summary=merged_references, **payload)

    def generate_brd(self, payload: Dict[str, str], references: List[str]) -> Dict[str, str]:
        prompt = self._format_prompt(payload, references)
        if self._client is None:
            if not self.settings.allow_mock_ai:
                raise BRDGenerationError("OpenAI client not available and mock responses disabled.")
            return self._mock_response(payload, references)

        try:  # pragma: no cover - network call
            response = self._client.responses.create(
                model=self.settings.model_name,
                input=prompt,
            )
        except Exception as exc:  # pragma: no cover
            if self.settings.allow_mock_ai:
                return self._mock_response(payload, references)
            raise BRDGenerationError(str(exc)) from exc

        content = response.output_text  # type: ignore[attr-defined]
        return {
            "brd_markdown": content,
            "mermaid_diagram": "",
            "gap_analysis": {},
            "stakeholder_summaries": {},
        }

    def _mock_response(self, payload: Dict[str, str], references: List[str]) -> Dict[str, str]:
        reference_summary = "\n".join(ref[:2000] for ref in references)
        brd_markdown = textwrap.dedent(
            f"""
            # {payload['project_name']} - Business Requirements Document

            ## Executive Summary
            This project addresses {payload['business_problem']} with the primary goal of {payload['goals']}. The initiative targets the {payload['industry']} industry and involves stakeholders: {payload['stakeholders']}.

            ## Business Objectives
            - Align project outcomes with stated goals.
            - Deliver measurable value within {payload['timelines']}.

            ## Scope
            **In Scope**
            - Core functional capabilities required to meet goals.

            **Out of Scope**
            - Items not aligned to MVP timeline.

            ## Functional Requirements
            1. System must support documentation ingestion and analysis.
            2. Platform generates BRDs using AI guidance.

            ## Non-Functional Requirements
            - Ensure data is stored securely on local infrastructure.

            ## Assumptions
            - Stakeholders will provide timely feedback.

            ## Constraints
            - Limited access to production-like data during MVP.

            ## Acceptance Criteria
            ```gherkin
            Scenario: Generate BRD draft
              Given a project with uploaded reference documents
              When the analyst triggers the AI generation
              Then a BRD draft is produced with key sections populated
            ```

            ## Risks & Mitigation Strategies
            - Risk: Delayed stakeholder approvals. Mitigation: Establish review checkpoints.

            ## Timeline Overview
            The project follows the stated timelines: {payload['timelines']}.

            ## Dependencies
            - Timely availability of SMEs and uploaded reference materials.

            ## Gap Analysis
            - Missing Information: Detailed performance requirements.
            - Clarifying Questions: What SLAs are expected post-launch?

            ## Stakeholder Summaries
            - Executives: Focus on strategic alignment and ROI.
            - Technical Team: Emphasize system integrations and data flows.
            - Non-Technical: Highlight user outcomes and rollout plan.

            ## Reference Highlights
            {reference_summary or 'No references provided.'}
            """
        ).strip()
        mermaid_diagram = textwrap.dedent(
            """
            ```mermaid
            mindmap
              root((Project Vision))
                Objectives
                  Deliver BRD automation
                  Support stakeholder collaboration
                Requirements
                  Functional
                    Document ingestion
                    AI draft generation
                  Non-Functional
                    Security
                    Performance
                Timeline
                  Planning
                  Execution
                  Launch
            ```
            """
        ).strip()
        gap_analysis = {
            "missing_information": ["Detailed reporting requirements", "Integration specifications"],
            "clarifying_questions": ["Are there compliance considerations?", "What user roles require access?"]
        }
        stakeholder_summaries = {
            "executives": "Concise overview highlighting strategic benefits and ROI expectations.",
            "technical_team": "Focus on integrations, data flows, and infrastructure impacts.",
            "non_technical": "Emphasize user experience improvements and training considerations.",
        }
        return {
            "brd_markdown": brd_markdown,
            "mermaid_diagram": mermaid_diagram,
            "gap_analysis": gap_analysis,
            "stakeholder_summaries": stakeholder_summaries,
        }


def generate_brd(payload: Dict[str, str], references: List[str]) -> Dict[str, str]:
    client = AIClient()
    return client.generate_brd(payload, references)
