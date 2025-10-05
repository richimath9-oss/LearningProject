# AI BRD Co-pilot

A full-stack MVP for generating Business Requirements Documents (BRDs) with AI assistance. The project includes a FastAPI backend for document ingestion, GPT-powered generation, and exports, along with a React + Tailwind frontend for analyst workflows.

## Features

- Project creation capturing industry context and goals
- Multi-file upload with support for DOCX, PDF, PPTX, XLSX/CSV, and EML/MSG
- AI-generated BRDs using the provided master prompt
- Automated gap analysis, MoSCoW prioritisation, and stakeholder summaries
- Mermaid.js visual requirement mapping with PNG/SVG ready markup
- Version history and diff endpoint
- Export to DOCX and PDF
- Dockerised backend and frontend, plus local dev instructions

## Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Docker & Docker Compose
- OpenAI API key (set `OPENAI_API_KEY` when available; mock responses are enabled by default)

## Backend setup

```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Environment variables:

- `OPENAI_API_KEY` – optional; enables live calls to OpenAI
- `DATA_DIR` – optional override for storage directory (default `./data`)

### Tests

```bash
cd app
pytest
```

## Frontend setup

```bash
cd web
npm install
npm run dev
```

The dev server expects the backend at `http://localhost:8000`. Override with `VITE_API_BASE_URL`.

## Docker Compose

```bash
docker-compose up --build
```

Backend available at `http://localhost:8000`, frontend at `http://localhost:5173`.

## Sample data

`docs/sample_project.json` demonstrates a typical payload, and `docs/sample_reference.txt` is an example reference document.

## CLI quickstart

1. Create and activate the Python virtual environment (`python -m venv .venv && source .venv/bin/activate`).
2. Install backend dependencies (`pip install -r app/requirements.txt`).
3. Run the backend (`uvicorn app.main:app --reload`).
4. Install frontend dependencies (`cd web && npm install`).
5. Start the frontend dev server (`npm run dev`).

## Known limitations

- AI generation falls back to deterministic mock content without an OpenAI key.
- File parsers rely on third-party libraries; ensure system dependencies (e.g., `libxml2`) are installed when building Docker images.
- Jira integration is stubbed.
