"""Shared fixtures: redirect the data dir to a temporary location."""
import pytest

from app.core.config import settings


@pytest.fixture()
def temp_data_dir(tmp_path):
    """Point all writable data paths at a fresh temp dir for the test."""
    original = {
        "data_dir": settings.data_dir,
        "projects_dir": settings.projects_dir,
        "templates_dir": settings.templates_dir,
        "exports_dir": settings.exports_dir,
        "library_db_path": settings.library_db_path,
    }
    settings.data_dir = tmp_path
    settings.projects_dir = tmp_path / "projects"
    settings.templates_dir = tmp_path / "templates"
    settings.exports_dir = tmp_path / "exports"
    settings.library_db_path = tmp_path / "library.db"
    settings.ensure_dirs()
    yield tmp_path
    for key, value in original.items():
        setattr(settings, key, value)
