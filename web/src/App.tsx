import { useMemo, useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "./lib/api";
import { DocumentMetadata, Project } from "./types";
import { DocumentIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false, theme: "dark" });

function MermaidRenderer({ diagram }: { diagram: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!diagram) return;
    const render = async () => {
      try {
        const { svg } = await mermaid.render("diagram", diagram.replace(/```mermaid|```/g, ""));
        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (err) {
        if (ref.current) {
          ref.current.innerHTML = `<pre class="text-red-400">${String(err)}</pre>`;
        }
      }
    };
    render();
  }, [diagram]);
  return <div ref={ref} className="bg-slate-900 rounded-lg p-4 overflow-auto" />;
}

function ProjectForm({ onCreate }: { onCreate: (project: Project) => void }) {
  const [form, setForm] = useState({
    name: "",
    industry: "",
    business_problem: "",
    goals: "",
    stakeholders: "",
    timelines: ""
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<Project>("/projects", form);
      return data;
    },
    onSuccess: onCreate
  });

  return (
    <form
      className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-900/70 p-6 rounded-xl"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
    >
      {Object.entries(form).map(([key, value]) => (
        <label key={key} className="flex flex-col text-sm">
          <span className="mb-1 font-semibold uppercase tracking-wide text-xs text-slate-300">{key.replace("_", " ")}</span>
          <input
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:ring focus:ring-emerald-500"
            value={value}
            onChange={(event) => setForm((prev) => ({ ...prev, [key]: event.target.value }))}
            required
          />
        </label>
      ))}
      <button
        type="submit"
        className="md:col-span-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-4 py-2 rounded-lg"
        disabled={mutation.isPending}
      >
        {mutation.isPending ? "Creating..." : "Create Project"}
      </button>
    </form>
  );
}

function FileUploader({ onUploadComplete }: { onUploadComplete: (docs: DocumentMetadata[]) => void }) {
  const [files, setFiles] = useState<FileList | null>(null);
  const mutation = useMutation({
    mutationFn: async () => {
      if (!files) return [];
      const formData = new FormData();
      Array.from(files).forEach((file) => formData.append("files", file));
      const { data } = await api.post<{ documents: DocumentMetadata[] }>("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return data.documents;
    },
    onSuccess: onUploadComplete
  });

  return (
    <div className="bg-slate-900/70 p-6 rounded-xl flex flex-col gap-3">
      <label className="border border-dashed border-slate-600 rounded-lg p-6 text-center cursor-pointer hover:border-emerald-400">
        <input
          type="file"
          className="hidden"
          multiple
          onChange={(event) => setFiles(event.target.files)}
          accept=".doc,.docx,.pdf,.ppt,.pptx,.csv,.xlsx,.xls,.eml,.msg"
        />
        <DocumentIcon className="w-12 h-12 mx-auto text-emerald-400" />
        <p className="mt-2 text-sm text-slate-300">Drop project references here or click to browse.</p>
      </label>
      <button
        className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-4 py-2 rounded-lg disabled:opacity-50"
        onClick={() => mutation.mutate()}
        disabled={!files || mutation.isPending}
      >
        {mutation.isPending ? "Uploading..." : "Upload Files"}
      </button>
      {mutation.isSuccess && (
        <p className="text-xs text-emerald-300">Uploaded {mutation.data?.length ?? 0} documents.</p>
      )}
    </div>
  );
}

function VersionList({ project, onSelect }: { project: Project; onSelect: (versionId: string) => void }) {
  if (!project.versions.length) return null;
  return (
    <div className="bg-slate-900/70 p-4 rounded-xl">
      <h3 className="text-sm font-semibold uppercase text-slate-400 mb-2">Versions</h3>
      <ul className="space-y-2">
        {project.versions.map((version) => (
          <li key={version.id}>
            <button
              className="w-full text-left px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700"
              onClick={() => onSelect(version.id)}
            >
              <div className="text-sm font-medium">{new Date(version.created_at).toLocaleString()}</div>
              <div className="text-xs text-slate-400">{version.gap_analysis.missing_information.length} gaps flagged</div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function BRDViewer({ project, versionId }: { project: Project | null; versionId: string | null }) {
  const version = useMemo(() => project?.versions.find((v) => v.id === versionId) ?? project?.versions[0], [project, versionId]);
  if (!project || !version) return null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-slate-900/80 p-6 rounded-xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">BRD Draft</h2>
          <ExportButtons projectId={project.id} versionId={version.id} />
        </div>
        <article className="prose prose-invert max-w-none text-sm leading-relaxed">
          <ReactMarkdown>{version.brd_markdown}</ReactMarkdown>
        </article>
        <div>
          <h3 className="font-semibold text-lg mb-2">Gap Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="uppercase text-xs tracking-wide text-slate-400">Missing Information</h4>
              <ul className="mt-2 space-y-1 list-disc list-inside">
                {version.gap_analysis.missing_information.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="uppercase text-xs tracking-wide text-slate-400">Clarifying Questions</h4>
              <ul className="mt-2 space-y-1 list-disc list-inside">
                {version.gap_analysis.clarifying_questions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
        {version.priority_matrix.length > 0 && (
          <div>
            <h3 className="font-semibold text-lg mb-2">MoSCoW Priorities</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="text-left text-xs uppercase text-slate-400">
                  <tr>
                    <th className="py-2 pr-4">Requirement</th>
                    <th className="py-2">Priority</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {version.priority_matrix.map((entry) => (
                    <tr key={`${entry.requirement}-${entry.priority}`}>
                      <td className="py-2 pr-4">{entry.requirement}</td>
                      <td className="py-2 font-semibold text-emerald-300">{entry.priority}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      <div className="space-y-4">
        <div className="bg-slate-900/80 p-6 rounded-xl">
          <h3 className="text-lg font-semibold mb-3">Requirement Map</h3>
          <MermaidRenderer diagram={version.mermaid_diagram} />
        </div>
        <div className="bg-slate-900/80 p-6 rounded-xl text-sm space-y-3">
          <h3 className="text-lg font-semibold">Stakeholder Summaries</h3>
          <div>
            <h4 className="font-semibold text-slate-300">Executives</h4>
            <p className="text-slate-300/80">{version.stakeholder_summaries.executives}</p>
          </div>
          <div>
            <h4 className="font-semibold text-slate-300">Technical Team</h4>
            <p className="text-slate-300/80">{version.stakeholder_summaries.technical_team}</p>
          </div>
          <div>
            <h4 className="font-semibold text-slate-300">Non-technical</h4>
            <p className="text-slate-300/80">{version.stakeholder_summaries.non_technical}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function ExportButtons({ projectId, versionId }: { projectId: string; versionId: string }) {
  const download = async (format: "pdf" | "docx") => {
    const response = await api.post(`/projects/${projectId}/export`, { version_id: versionId, export_format: format }, { responseType: "blob" });
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `BRD.${format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-2">
      <button className="px-3 py-1.5 bg-slate-800 rounded-lg text-xs" onClick={() => download("docx")}>Export DOCX</button>
      <button className="px-3 py-1.5 bg-slate-800 rounded-lg text-xs" onClick={() => download("pdf")}>Export PDF</button>
    </div>
  );
}

function GenerateButton({ projectId, documentIds, onGenerated }: { projectId: string; documentIds: string[]; onGenerated: () => void }) {
  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/projects/${projectId}/generate`, { document_ids: documentIds });
      return data;
    },
    onSuccess: onGenerated
  });

  return (
    <button
      className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold px-4 py-2 rounded-lg disabled:opacity-50 flex items-center gap-2"
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
    >
      {mutation.isPending && <ArrowPathIcon className="w-4 h-4 animate-spin" />}
      {mutation.isPending ? "Generating" : "Generate BRD"}
    </button>
  );
}

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);

  const refreshProject = async (projectId: string) => {
    const { data } = await api.get<Project>(`/projects/${projectId}`);
    setProject(data);
    if (data.versions.length) {
      setSelectedVersion(data.versions[0].id);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <header className="max-w-6xl mx-auto py-10 px-4">
        <h1 className="text-3xl font-bold">AI Business Requirements Co-pilot</h1>
        <p className="text-slate-400 mt-2 max-w-2xl">
          Create structured BRDs, visualize requirement hierarchies, and export stakeholder-ready documentation in minutes.
        </p>
      </header>
      <main className="max-w-6xl mx-auto px-4 pb-16 space-y-8">
        {!project ? (
          <ProjectForm
            onCreate={(created) => {
              setProject(created);
              setSelectedVersion(null);
            }}
          />
        ) : (
          <div className="space-y-6">
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <FileUploader onUploadComplete={setDocuments} />
              <div className="bg-slate-900/70 p-6 rounded-xl space-y-3 lg:col-span-2">
                <h2 className="text-lg font-semibold">Project Overview</h2>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-slate-300">
                  <div>
                    <dt className="uppercase text-xs tracking-wide text-slate-500">Industry</dt>
                    <dd>{project.industry}</dd>
                  </div>
                  <div>
                    <dt className="uppercase text-xs tracking-wide text-slate-500">Goals</dt>
                    <dd>{project.goals}</dd>
                  </div>
                  <div>
                    <dt className="uppercase text-xs tracking-wide text-slate-500">Stakeholders</dt>
                    <dd>{project.stakeholders}</dd>
                  </div>
                  <div>
                    <dt className="uppercase text-xs tracking-wide text-slate-500">Timeline</dt>
                    <dd>{project.timelines}</dd>
                  </div>
                </dl>
                <GenerateButton
                  projectId={project.id}
                  documentIds={documents.map((doc) => doc.id)}
                  onGenerated={() => refreshProject(project.id)}
                />
              </div>
            </section>
            <section className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-1">
                <VersionList project={project} onSelect={setSelectedVersion} />
              </div>
              <div className="lg:col-span-3">
                <BRDViewer project={project} versionId={selectedVersion} />
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
