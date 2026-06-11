"""Health and version endpoints used by the Electron launcher."""
from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings
from app.core.responses import ok
from app.services.bible_service import bible_service

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return ok({"status": "ok"})


@router.get("/version")
def version() -> dict:
    return ok(
        {
            "name": settings.APP_NAME,
            "version": __version__,
            "capabilities": {
                "bible": bible_service.is_available(),
                "sectionTypes": [
                    "cover",
                    "responsive_reading",
                    "scripture",
                    "hymn",
                    "liturgy_text",
                    "announcement",
                    "media",
                ],
                "exportSectionTypes": [
                    "cover",
                    "responsive_reading",
                    "scripture",
                    "hymn",
                    "liturgy_text",
                    "announcement",
                    "media",
                ],
                "libraries": True,
                "themes": True,
                "media": True,
                "templateImportExport": True,
                "audioPlayback": False,
            },
        }
    )
