"""Tests for template save-from-project and import/export with media."""
import json

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import templates as templates_api
from app.core.errors import AppError
from app.domain.media import MediaAsset
from app.domain.project import Project
from app.domain.sections import AnnouncementSection, CoverSection, MediaSection
from app.domain.style import SectionStyle, TextStyle
from app.main import create_app
from app.services import media_store
from app.services.generation import build_section_slides
from app.services.project_store import ProjectStore
from app.services.template_store import TemplateStore


def _project_with_media(tmp_path) -> tuple[Project, "Path"]:
    work = tmp_path / "proj"
    work.mkdir()
    media = media_store.media_dir(work)
    (media / "bg.png").write_bytes(b"BGDATA")
    project = Project(
        name="测试工程",
        sections=[CoverSection(style=SectionStyle(background_image="media/bg.png"))],
    )
    return project, work


def test_from_project_copies_media(temp_data_dir, tmp_path):
    store = TemplateStore()
    project, src_dir = _project_with_media(tmp_path)
    tpl = store.from_project(project, src_dir, name="我的模板")
    assert not tpl.builtin
    wd = store.work_dir(tpl.id)
    assert wd is not None
    assert (wd / "media" / "bg.png").read_bytes() == b"BGDATA"


def test_export_import_roundtrip_with_media(temp_data_dir, tmp_path):
    store = TemplateStore()
    project, src_dir = _project_with_media(tmp_path)
    tpl = store.from_project(project, src_dir, name="可分享模板")

    out = tmp_path / "share.lumina"
    store.export(tpl.id, out)
    assert out.exists()

    imported = store.import_(out)
    assert imported.id != tpl.id
    assert not imported.builtin
    wd = store.work_dir(imported.id)
    assert (wd / "media" / "bg.png").read_bytes() == b"BGDATA"
    # The background image ref is preserved and resolvable.
    ref = imported.sections[0].style.background_image
    assert media_store.media_path(wd, ref).exists()


def test_template_carries_unreferenced_media_assets(temp_data_dir, tmp_path):
    store = TemplateStore()
    work = tmp_path / "proj"
    work.mkdir()
    media = media_store.media_dir(work)
    (media / "video.mp4").write_bytes(b"VIDEODATA")
    project = Project(
        name="资源库模板",
        media_assets=[
            MediaAsset(
                kind="video",
                name="预留视频",
                ref="media/video.mp4",
            )
        ],
    )

    tpl = store.from_project(project, work, name="带资源库模板")
    wd = store.work_dir(tpl.id)
    assert wd is not None
    assert tpl.media_assets[0].name == "预留视频"
    assert (wd / "media" / "video.mp4").read_bytes() == b"VIDEODATA"

    out = tmp_path / "media-assets.lumina"
    store.export(tpl.id, out)
    imported = store.import_(out)
    imported_wd = store.work_dir(imported.id)
    assert imported.media_assets[0].ref == "media/video.mp4"
    assert (imported_wd / "media" / "video.mp4").read_bytes() == b"VIDEODATA"


def test_project_created_from_template_copies_media_assets(temp_data_dir, tmp_path):
    store = TemplateStore()
    work = tmp_path / "proj"
    work.mkdir()
    media = media_store.media_dir(work)
    (media / "bg.png").write_bytes(b"BGDATA")
    project = Project(
        name="模板源",
        media_assets=[
            MediaAsset(kind="image", name="背景图", ref="media/bg.png")
        ],
    )
    tpl = store.from_project(project, work, name="资源模板")

    project_store = ProjectStore()
    created = project_store.create(template_id=tpl.id)
    wd = project_store.work_dir(created.id)
    assert created.media_assets[0].name == "背景图"
    assert (wd / "media" / "bg.png").read_bytes() == b"BGDATA"


def test_builtin_template_readonly(temp_data_dir):
    store = TemplateStore()

    with pytest.raises(AppError):
        store.delete("builtin-sunday")
    copy = store.duplicate("builtin-sunday")
    assert not copy.builtin


def test_builtin_template_media_sections_use_body(temp_data_dir):
    store = TemplateStore()
    template = store.get("builtin-sunday")
    assert template is not None

    media_sections = [
        section for section in template.sections if isinstance(section, MediaSection)
    ]
    assert media_sections[0].title == "起立默祷"
    assert media_sections[0].slide_title == "起立默祷"
    assert media_sections[0].body == "请起立默祷"


def test_project_created_from_builtin_template_keeps_announcement_heading(
    temp_data_dir,
):
    project = ProjectStore().create(template_id="builtin-sunday")
    announcement = next(
        section
        for section in project.sections
        if isinstance(section, AnnouncementSection)
    )

    assert announcement.title == "家事报告"
    assert announcement.heading == "家事报告"
    assert build_section_slides(announcement)[0].title == "家事报告"


def test_font_style_survives_template_copy_and_container_roundtrip(
    temp_data_dir, tmp_path
):
    store = TemplateStore()
    project = Project(
        name="字体模板",
        sections=[
            CoverSection(
                style=SectionStyle(
                    title=TextStyle(
                        bold=False,
                        italic=True,
                        underline=True,
                        color="#123456",
                        highlight_color="#FFF200",
                    )
                )
            )
        ],
    )
    template = store.from_project(project, None)
    copied = store.duplicate(template.id)
    copied_style = copied.sections[0].style.title
    assert copied_style.bold is False
    assert copied_style.italic is True
    assert copied_style.underline is True
    assert copied_style.highlight_color == "#FFF200"

    out = tmp_path / "font-style.lumina"
    store.export(copied.id, out)
    imported = store.import_(out)
    imported_style = imported.sections[0].style.title
    assert imported_style.color == "#123456"
    assert imported_style.highlight_color == "#FFF200"


def test_rename_template_trims_and_only_changes_persisted_name(
    temp_data_dir, tmp_path
):
    store = TemplateStore()
    project, src_dir = _project_with_media(tmp_path)
    project.media_assets = [
        MediaAsset(kind="image", name="背景图", ref="media/bg.png")
    ]
    template = store.from_project(project, src_dir, name="原模板")
    project_store = ProjectStore()
    existing_project = project_store.create(template_id=template.id, name="已建工程")
    original_template = store.get(template.id).model_dump()
    original_project = existing_project.model_dump()
    template_dir = store.work_dir(template.id)
    media_path = template_dir / "media" / "bg.png"
    original_media = media_path.read_bytes()
    original_json = json.loads((template_dir / "template.json").read_text())

    renamed = store.rename(template.id, "  新模板  ")

    assert renamed.name == "新模板"
    renamed_without_name = renamed.model_dump()
    renamed_without_name.pop("name")
    original_template.pop("name")
    assert renamed_without_name == original_template
    renamed_json = json.loads((template_dir / "template.json").read_text())
    assert renamed_json.pop("name") == "新模板"
    original_json.pop("name")
    assert renamed_json == original_json
    assert media_path.read_bytes() == original_media
    assert project_store.get(existing_project.id).model_dump() == original_project

    reloaded = TemplateStore().get(template.id)
    assert reloaded is not None
    assert reloaded.name == "新模板"


@pytest.mark.parametrize("name", ["", "   \t\n"])
def test_rename_template_rejects_blank_name(temp_data_dir, name):
    store = TemplateStore()
    template = store.from_project(Project(), None, name="原模板")

    with pytest.raises(AppError, match="模板名称不能为空"):
        store.rename(template.id, name)

    assert store.get(template.id).name == "原模板"


def test_rename_builtin_template_is_readonly(temp_data_dir):
    with pytest.raises(AppError, match="内置流程模板为只读，请先复制后再编辑"):
        TemplateStore().rename("builtin-sunday", "新名称")


def test_rename_template_api_contract(temp_data_dir, monkeypatch):
    store = TemplateStore()
    template = store.from_project(Project(), None, name="API 模板")
    monkeypatch.setattr(templates_api, "template_store", store)
    client = TestClient(create_app())

    response = client.patch(
        f"/api/v1/service-templates/{template.id}", json={"name": "  新 API 模板  "}
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == template.id
    assert response.json()["data"]["name"] == "新 API 模板"
    detail = client.get(f"/api/v1/service-templates/{template.id}")
    assert detail.json()["data"]["name"] == "新 API 模板"
    listed = client.get("/api/v1/service-templates").json()["data"]
    assert next(item for item in listed if item["id"] == template.id)["name"] == (
        "新 API 模板"
    )

    blank = client.patch(
        f"/api/v1/service-templates/{template.id}", json={"name": "   "}
    )
    assert blank.status_code == 400
    assert blank.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "模板名称不能为空",
        "details": None,
    }

    builtin = client.patch(
        "/api/v1/service-templates/builtin-sunday", json={"name": "新名称"}
    )
    assert builtin.status_code == 400
    assert builtin.json()["error"]["message"] == (
        "内置流程模板为只读，请先复制后再编辑"
    )

    missing = client.patch(
        "/api/v1/service-templates/missing", json={"name": "新名称"}
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"
