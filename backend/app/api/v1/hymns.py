"""Hymn library endpoints: search, detail, CRUD, duplicate, import/export."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.responses import ok
from app.domain.library import Hymn, hymn_summary
from app.services.hymn_store import hymn_store

router = APIRouter(prefix="/hymns", tags=["hymns"])


class ExportHymnLibraryBody(BaseModel):
    path: Optional[str] = None


class ImportHymnLibraryBody(BaseModel):
    path: str


def _safe_filename(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
    return cleaned or "hymn-library"


@router.get("")
def list_hymns(query: str = "") -> dict:
    return ok([hymn_summary(h).model_dump() for h in hymn_store.search(query)])


@router.post("/export")
def export_hymn_library(body: ExportHymnLibraryBody) -> dict:
    if body.path:
        out = Path(body.path)
    else:
        settings.ensure_dirs()
        out = settings.exports_dir / f"{_safe_filename('歌词库')}.lumina-hymn"
    saved, count = hymn_store.export_library(out)
    return ok({"path": str(saved), "count": count})


@router.post("/import")
def import_hymn_library(body: ImportHymnLibraryBody) -> dict:
    items = hymn_store.import_library(Path(body.path))
    return ok({"imported": len(items), "items": [h.model_dump() for h in items]})


@router.get("/{hymn_id}")
def get_hymn(hymn_id: str) -> dict:
    return ok(hymn_store.get(hymn_id).model_dump())


@router.post("")
def create_hymn(hymn: Hymn) -> dict:
    return ok(hymn_store.create(hymn).model_dump())


@router.put("/{hymn_id}")
def update_hymn(hymn_id: str, hymn: Hymn) -> dict:
    return ok(hymn_store.update(hymn_id, hymn).model_dump())


@router.delete("/{hymn_id}")
def delete_hymn(hymn_id: str) -> dict:
    hymn_store.delete(hymn_id)
    return ok({"deleted": hymn_id})


@router.post("/{hymn_id}/duplicate")
def duplicate_hymn(hymn_id: str) -> dict:
    return ok(hymn_store.duplicate(hymn_id).model_dump())
