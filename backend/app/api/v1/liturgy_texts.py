"""Liturgy-text library endpoints: list, detail, CRUD, duplicate."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.responses import ok
from app.domain.library import LiturgyText, liturgy_summary
from app.services.liturgy_store import liturgy_store

router = APIRouter(prefix="/liturgy-texts", tags=["liturgy"])


@router.get("")
def list_texts(query: str = "") -> dict:
    return ok([liturgy_summary(t).model_dump() for t in liturgy_store.list(query)])


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
