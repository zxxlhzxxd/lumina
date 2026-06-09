"""Service (worship-flow) template endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.errors import NotFoundError
from app.core.responses import ok
from app.services.template_store import template_store

router = APIRouter(prefix="/service-templates", tags=["templates"])


@router.get("")
def list_templates() -> dict:
    return ok(
        [
            {
                "id": t.id,
                "name": t.name,
                "builtin": t.builtin,
                "description": t.description,
                "section_count": len(t.sections),
            }
            for t in template_store.list_templates()
        ]
    )


@router.get("/{template_id}")
def get_template(template_id: str) -> dict:
    template = template_store.get(template_id)
    if template is None:
        raise NotFoundError(f"流程模板不存在: {template_id}")
    return ok(template.model_dump())
