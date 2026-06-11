"""Hymn library endpoints: search, detail, CRUD, duplicate."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.responses import ok
from app.domain.library import Hymn, hymn_summary
from app.services.hymn_store import hymn_store

router = APIRouter(prefix="/hymns", tags=["hymns"])


@router.get("")
def list_hymns(query: str = "") -> dict:
    return ok([hymn_summary(h).model_dump() for h in hymn_store.search(query)])


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
