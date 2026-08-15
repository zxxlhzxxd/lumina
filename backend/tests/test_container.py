"""Tests for zip container pack/unpack and media helpers."""
import json
import zipfile

import pytest

from app.domain.sections import CoverSection, MediaSection
from app.domain.style import SectionStyle
from app.services import container, media_store
from app.core.errors import AppError
from app.services.project_store import ProjectStore


def test_pack_unpack_roundtrip(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "project.json").write_text('{"name":"x"}', encoding="utf-8")
    media = media_store.media_dir(work)
    (media / "pic.png").write_bytes(b"PNGDATA")

    out = tmp_path / "out.lumina"
    container.pack(work, "project.json", out, kind="project")
    assert out.exists()

    dest = tmp_path / "dest"
    manifest = container.unpack(out, dest)
    assert manifest["kind"] == "project"
    assert (dest / "project.json").exists()
    assert (dest / "media" / "pic.png").read_bytes() == b"PNGDATA"


def _write_versioned_container(path, version=1):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps({"kind": "template", "schema_version": version}),
        )
        zf.writestr("template.json", json.dumps({"name": "旧模板"}))


def test_versioned_unpack_runs_complete_migration_chain(tmp_path):
    source = tmp_path / "old.lumina"
    _write_versioned_container(source)
    calls = []

    def migrate_v1(context):
        calls.append(1)
        payload = json.loads((context.work_dir / "template.json").read_text())
        payload["description"] = "v2"
        (context.work_dir / "template.json").write_text(json.dumps(payload))

    def migrate_v2(context):
        calls.append(2)
        (context.work_dir / "media").mkdir()
        (context.work_dir / "media" / "marker.txt").write_text("v3")

    dest = tmp_path / "imported"
    manifest = container.unpack_versioned(
        source,
        dest,
        expected_kind="template",
        current_version=3,
        migrations={1: migrate_v1, 2: migrate_v2},
    )

    assert calls == [1, 2]
    assert manifest["schema_version"] == 3
    assert json.loads((dest / "manifest.json").read_text())["schema_version"] == 3
    assert json.loads((dest / "template.json").read_text())["description"] == "v2"
    assert (dest / "media" / "marker.txt").read_text() == "v3"


def test_versioned_unpack_preflights_complete_migration_chain(tmp_path):
    source = tmp_path / "old.lumina"
    _write_versioned_container(source)
    calls = []
    dest = tmp_path / "imported"

    with pytest.raises(AppError, match="缺少版本 2 到版本 3 的迁移"):
        container.unpack_versioned(
            source,
            dest,
            expected_kind="template",
            current_version=3,
            migrations={1: lambda context: calls.append(context)},
        )

    assert calls == []
    assert not dest.exists()


def test_versioned_unpack_cleans_up_failed_migration(tmp_path):
    source = tmp_path / "old.lumina"
    _write_versioned_container(source)
    dest = tmp_path / "imported"

    def fail(context):
        (context.work_dir / "partial.txt").write_text("partial")
        raise RuntimeError("boom")

    with pytest.raises(AppError, match="版本 1 迁移到版本 2 失败") as exc_info:
        container.unpack_versioned(
            source,
            dest,
            expected_kind="template",
            current_version=2,
            migrations={1: fail},
        )

    assert exc_info.value.details == {"source_version": 1, "target_version": 2}
    assert not dest.exists()


def test_versioned_unpack_rejects_bad_zip_without_creating_destination(tmp_path):
    source = tmp_path / "bad.lumina"
    source.write_bytes(b"not-a-zip")
    dest = tmp_path / "imported"

    with pytest.raises(AppError, match="非 zip 格式"):
        container.unpack_versioned(
            source,
            dest,
            expected_kind="template",
            current_version=1,
            migrations={},
        )

    assert not dest.exists()


def test_collect_and_rewrite_media_refs():
    sections = [
        CoverSection(style=SectionStyle(background_image="media/bg.jpg")),
        MediaSection(audio_ref="media/song.mp3"),
        MediaSection(audio_ref=None),
    ]
    refs = media_store.collect_media_refs(sections)
    assert set(refs) == {"media/bg.jpg", "media/song.mp3"}

    media_store.rewrite_media_refs(
        sections, {"media/bg.jpg": "media/new.jpg", "media/song.mp3": "media/x.mp3"}
    )
    assert sections[0].style.background_image == "media/new.jpg"
    assert sections[1].audio_ref == "media/x.mp3"


def test_import_media(tmp_path):
    src = tmp_path / "source.png"
    src.write_bytes(b"IMG")
    work = tmp_path / "work"
    work.mkdir()
    ref = media_store.import_media(work, str(src))
    assert ref == "media/source.png"
    assert media_store.media_path(work, ref).read_bytes() == b"IMG"


def test_import_media_rejects_wrong_kind(tmp_path):
    src = tmp_path / "source.png"
    src.write_bytes(b"IMG")
    work = tmp_path / "work"
    work.mkdir()
    import pytest

    with pytest.raises(AppError):
        media_store.import_media(work, str(src), kind="audio")


def test_project_delete_media_blocks_used_refs(temp_data_dir, tmp_path):
    src = tmp_path / "song.wav"
    src.write_bytes(b"AUDIO")
    store = ProjectStore()
    project = store.create(name="媒体工程")
    asset = store.import_media(project.id, str(src), kind="audio")
    project.sections = [MediaSection(audio_ref=asset.ref)]
    store.write_file(project)
    import pytest

    with pytest.raises(AppError):
        store.delete_media(project.id, "song.wav")
