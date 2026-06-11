"""Visual-theme endpoints: list, detail, CRUD, duplicate, set-default."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import NotFoundError
from app.core.responses import ok
from app.domain.project import Theme
from app.services.theme_store import theme_store

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("")
def list_themes() -> dict:
    default_id = theme_store.default_id
    return ok(
        {
            "default_id": default_id,
            "themes": [
                {
                    "id": t.id,
                    "name": t.name,
                    "builtin": t.builtin,
                    "is_default": t.id == default_id,
                }
                for t in theme_store.list()
            ],
        }
    )


@router.get("/{theme_id}")
def get_theme(theme_id: str) -> dict:
    theme = theme_store.get(theme_id)
    if theme is None:
        raise NotFoundError(f"主题不存在: {theme_id}")
    return ok(theme.model_dump())


@router.post("")
def create_theme(theme: Theme) -> dict:
    return ok(theme_store.create(theme).model_dump())


@router.put("/{theme_id}")
def update_theme(theme_id: str, theme: Theme) -> dict:
    return ok(theme_store.update(theme_id, theme).model_dump())


@router.delete("/{theme_id}")
def delete_theme(theme_id: str) -> dict:
    theme_store.delete(theme_id)
    return ok({"deleted": theme_id})


@router.post("/{theme_id}/duplicate")
def duplicate_theme(theme_id: str) -> dict:
    return ok(theme_store.duplicate(theme_id).model_dump())


@router.post("/{theme_id}/set-default")
def set_default(theme_id: str) -> dict:
    return ok({"default_id": theme_store.set_default(theme_id)})
