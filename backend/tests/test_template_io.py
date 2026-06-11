"""Tests for template save-from-project and import/export with media."""
from app.domain.project import Project
from app.domain.sections import CoverSection
from app.domain.style import SectionStyle
from app.services import media_store
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

    out = tmp_path / "share.lumina-template"
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


def test_builtin_template_readonly(temp_data_dir):
    store = TemplateStore()
    import pytest
    from app.core.errors import AppError

    with pytest.raises(AppError):
        store.delete("builtin-sunday")
    copy = store.duplicate("builtin-sunday")
    assert not copy.builtin
