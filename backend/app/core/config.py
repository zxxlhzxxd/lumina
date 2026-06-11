"""Runtime configuration for the Lumina backend.

All settings are environment-driven so the Electron shell can control the
backend subprocess (host/port) without code changes.
"""
from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """Simple env-backed settings (no external deps)."""

    APP_NAME: str = "Lumina"

    def __init__(self) -> None:
        self.host: str = os.environ.get("LUMINA_HOST", "127.0.0.1")
        # 0 lets the OS pick a free port; the launcher reads it back from stdout.
        self.port: int = int(os.environ.get("LUMINA_PORT", "0"))

        # Base directory for user data (projects, templates, themes).
        default_data_dir = Path.home() / ".lumina"
        self.data_dir: Path = Path(os.environ.get("LUMINA_DATA_DIR", str(default_data_dir)))

        # Directory of bundled application data (bible.sqlite, seed templates).
        self.app_data_dir: Path = Path(__file__).resolve().parent.parent / "data"

        self.bible_db_path: Path = Path(
            os.environ.get("LUMINA_BIBLE_DB", str(self.app_data_dir / "bible.sqlite"))
        )

        # Content library (hymns + liturgy texts); seeded with built-ins on first run.
        self.library_db_path: Path = Path(
            os.environ.get("LUMINA_LIBRARY_DB", str(self.data_dir / "library.db"))
        )

        # Working stores: each project/template lives in its own directory holding
        # `project.json`/`template.json` + a `media/` subdirectory.
        self.projects_dir: Path = self.data_dir / "projects"
        self.templates_dir: Path = self.data_dir / "templates"
        self.themes_dir: Path = self.data_dir / "themes"
        self.exports_dir: Path = self.data_dir / "exports"

        # Small JSON file for user preferences (e.g. default theme id).
        self.prefs_path: Path = self.data_dir / "preferences.json"

    def ensure_dirs(self) -> None:
        for d in (
            self.data_dir,
            self.projects_dir,
            self.templates_dir,
            self.themes_dir,
            self.exports_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
