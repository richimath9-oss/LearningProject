from pathlib import Path

from app.core.config import get_settings
from app.services.storage import ProjectRepository


def test_project_create_and_retrieve(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    get_settings.cache_clear()  # type: ignore[attr-defined]
    repo = ProjectRepository()
    project = repo.create(
        {
            "name": "Test",
            "industry": "Tech",
            "business_problem": "Problem",
            "goals": "Goals",
            "stakeholders": "Stakeholders",
            "timelines": "Q1",
        }
    )
    fetched = repo.get(project.id)
    assert fetched.name == "Test"
    assert fetched.industry == "Tech"
