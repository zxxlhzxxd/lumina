"""Liturgy-text library endpoints: list, detail, CRUD, duplicate, import/export."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.responses import ok
from app.domain.library import LiturgyText, liturgy_summary
from app.services.liturgy_store import liturgy_store

router = APIRouter(prefix="/liturgy-texts", tags=["liturgy"])


class ExportLiturgyLibraryBody(BaseModel):
    path: Optional[str] = None


class ImportLiturgyLibraryBody(BaseModel):
    path: str


def _safe_filename(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
    return cleaned or "liturgy-library"


@router.get("")
def list_texts(query: str = "") -> dict:
    return ok([liturgy_summary(t).model_dump() for t in liturgy_store.list(query)])


@router.post("/export")
def export_liturgy_library(body: ExportLiturgyLibraryBody) -> dict:
    if body.path:
        out = Path(body.path)
    else:
        settings.ensure_dirs()
        out = settings.exports_dir / f"{_safe_filename('礼文库')}.lumina-liturgy"
    saved, count = liturgy_store.export_library(out)
    return ok({"path": str(saved), "count": count})


@router.post("/import")
def import_liturgy_library(body: ImportLiturgyLibraryBody) -> dict:
    items = liturgy_store.import_library(Path(body.path))
    return ok({"imported": len(items), "items": [t.model_dump() for t in items]})


@router.get("/{text_id}")
def get_text(text_id: str) -> dict:
    return ok(liturgy_store.get(text_id).model_dump())


@router.post("")
def create_text(text: LiturgyText) -> dict:
    return ok(liturgy_store.create(text).model_dump())


@router.put("/{text_id}")
def update_text(text_id: str, text: LiturgyText) -> dict:
    return ok(liturgy_store.update(text_id, text).model_dump())


@router.delete("/{text_id}")
def delete_text(text_id: str) -> dict:
    liturgy_store.delete(text_id)
    return ok({"deleted": text_id})


@router.post("/{text_id}/duplicate")
def duplicate_text(text_id: str) -> dict:
    return ok(liturgy_store.duplicate(text_id).model_dump())
