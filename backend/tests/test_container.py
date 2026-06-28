"""Tests for zip container pack/unpack and media helpers."""
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
