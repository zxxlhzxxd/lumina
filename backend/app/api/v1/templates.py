"""Service (worship-flow) template endpoints: CRUD, duplicate, save-from-project,
import/export (containers bundle all media)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.errors import NotFoundError
from app.core.responses import ok
from app.domain.project import ServiceTemplate
from app.services.project_store import project_store
from app.services.template_store import template_store
from app.core.config import settings

router = APIRouter(prefix="/service-templates", tags=["templates"])


class FromProjectBody(BaseModel):
    project_id: str
    name: Optional[str] = None
    description: str = ""


class ExportTemplateBody(BaseModel):
    path: Optional[str] = None


class ImportTemplateBody(BaseModel):
    path: str


def _summary(t: ServiceTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "builtin": t.builtin,
        "description": t.description,
        "section_count": len(t.sections),
    }


def _safe_filename(name: str) -> str:
    cleaned = "".join(c for c in name if c not in '\\/:*?"<>|').strip()
    return cleaned or "template"


@router.get("")
def list_templates() -> dict:
    return ok([_summary(t) for t in template_store.list_templates()])


@router.post("")
def create_template(template: ServiceTemplate) -> dict:
    return ok(template_store.create(template).model_dump())


@router.post("/from-project")
def from_project(body: FromProjectBody) -> dict:
    project = project_store.get(body.project_id)
    media_dir = project_store.work_dir(body.project_id)
    template = template_store.from_project(
        project, media_dir, name=body.name, description=body.description
    )
    return ok(template.model_dump())


@router.post("/import")
def import_template(body: ImportTemplateBody) -> dict:
    template = template_store.import_(Path(body.path))
    return ok(template.model_dump())


@router.get("/{template_id}")
def get_template(template_id: str) -> dict:
    template = template_store.get(template_id)
    if template is None:
        raise NotFoundError(f"流程模板不存在: {template_id}")
    return ok(template.model_dump())


@router.put("/{template_id}")
def update_template(template_id: str, template: ServiceTemplate) -> dict:
    return ok(template_store.update(template_id, template).model_dump())


@router.delete("/{template_id}")
def delete_template(template_id: str) -> dict:
    template_store.delete(template_id)
    return ok({"deleted": template_id})


@router.post("/{template_id}/duplicate")
def duplicate_template(template_id: str) -> dict:
    return ok(template_store.duplicate(template_id).model_dump())


@router.post("/{template_id}/export")
def export_template(template_id: str, body: ExportTemplateBody) -> dict:
    template = template_store.get(template_id)
    if template is None:
        raise NotFoundError(f"流程模板不存在: {template_id}")
    if body.path:
        out = Path(body.path)
    else:
        settings.ensure_dirs()
        out = settings.exports_dir / f"{_safe_filename(template.name)}.lumina"
    saved = template_store.export(template_id, out)
    return ok({"path": str(saved)})


@router.get("/{template_id}/export/download")
def export_template_download(template_id: str):
    template = template_store.get(template_id)
    if template is None:
        raise NotFoundError(f"流程模板不存在: {template_id}")
    settings.ensure_dirs()
    out = settings.exports_dir / f"{_safe_filename(template.name)}.lumina"
    saved = template_store.export(template_id, out)
    return FileResponse(
        str(saved), media_type="application/zip", filename=saved.name
    )
