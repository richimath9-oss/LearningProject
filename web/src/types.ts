export interface PriorityEntry {
  requirement: string;
  priority: string;
}

export interface DocumentMetadata {
  id: string;
  filename: string;
  content_type: string;
  text_preview: string;
  metadata: Record<string, string>;
}

export interface ProjectVersion {
  id: string;
  created_at: string;
  brd_markdown: string;
  mermaid_diagram: string;
  gap_analysis: {
    missing_information: string[];
    clarifying_questions: string[];
  };
  stakeholder_summaries: {
    executives: string;
    technical_team: string;
    non_technical: string;
  };
  priority_matrix: PriorityEntry[];
}

export interface Project {
  id: string;
  name: string;
  industry: string;
  business_problem: string;
  goals: string;
  stakeholders: string;
  timelines: string;
  created_at: string;
  updated_at: string;
  document_ids: string[];
  versions: ProjectVersion[];
}
