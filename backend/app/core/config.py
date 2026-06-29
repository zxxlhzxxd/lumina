"""Runtime configuration for the Lumina backend.

All settings are environment-driven so the Electron shell can control the
backend subprocess (host/port) without code changes.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


class Settings:
    """Simple env-backed settings (no external deps)."""

    APP_NAME: str = "Lumina"

    def __init__(self) -> None:
        self.host: str = os.environ.get("LUMINA_HOST", "127.0.0.1")
        # 0 lets the OS pick a free port; the launcher reads it back from stdout.
        self.port: int = int(os.environ.get("LUMINA_PORT", "0"))

        # Base directory for user data (projects and templates).
        default_data_dir = Path.home() / ".lumina"
        self.data_dir: Path = Path(os.environ.get("LUMINA_DATA_DIR", str(default_data_dir)))

        # Directory of bundled application data (bible.sqlite, seed templates).
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            self.app_data_dir: Path = Path(sys._MEIPASS) / "app" / "data"
        else:
            self.app_data_dir = Path(__file__).resolve().parent.parent / "data"

        self.bible_db_path: Path = Path(
            os.environ.get("LUMINA_BIBLE_DB", str(self.app_data_dir / "bible.sqlite"))
        )

        # Content library (hymns + liturgy texts).
        self.library_db_path: Path = Path(
            os.environ.get("LUMINA_LIBRARY_DB", str(self.data_dir / "library.db"))
        )

        # Working stores: each project/template lives in its own directory holding
        # `project.json`/`template.json` + a `media/` subdirectory.
        self.projects_dir: Path = self.data_dir / "projects"
        self.templates_dir: Path = self.data_dir / "templates"
        self.exports_dir: Path = self.data_dir / "exports"

    def ensure_dirs(self) -> None:
        for d in (
            self.data_dir,
            self.projects_dir,
            self.templates_dir,
            self.exports_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
