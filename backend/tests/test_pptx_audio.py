"""Tests for visible, editable audio embedding in exported PPTX."""
from __future__ import annotations

import math
import re
import hashlib
import struct
import wave
import zipfile
from pathlib import Path

import pytest
from PIL import Image
from pptx import Presentation

from app.core.errors import ExportError
from app.domain.project import Project
from app.domain.sections import MediaSection
from app.pptx.builder import AUDIO_SPEAKER_ICON
from app.pptx.builder import build_pptx
from app.services import media_store
from app.services.export_service import export_project, validate_project
from app.services.generation import SlideModel


def _write_wav(path: Path) -> None:
    framerate = 8000
    frames = []
    for i in range(framerate // 10):
        sample = int(12000 * math.sin(2 * math.pi * 440 * i / framerate))
        frames.append(struct.pack("<h", sample))
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(framerate)
        f.writeframes(b"".join(frames))


def _build_audio_pptx(
    tmp_path: Path,
    play_mode: str,
    audio_trigger: str = "click",
) -> tuple[Path, str, str, str]:
    work = tmp_path / f"work-{play_mode}-{audio_trigger}"
    media = media_store.media_dir(work)
    _write_wav(media / "tone.wav")
    out = tmp_path / f"audio-{play_mode}-{audio_trigger}.pptx"
    build_pptx(
        [
            SlideModel(
                kind="media",
                section_id="s1",
                section_type="media",
                body="请起立默祷",
                audio_ref="media/tone.wav",
                play_mode=play_mode,
                audio_trigger=audio_trigger,
            )
        ],
        out,
        media_root=work,
    )
    with zipfile.ZipFile(out) as z:
        content_types = z.read("[Content_Types].xml").decode("utf-8")
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")
        rels_xml = z.read("ppt/slides/_rels/slide1.xml.rels").decode("utf-8")
    return out, content_types, slide_xml, rels_xml


def test_audio_is_embedded_and_plays_on_click_sequence(tmp_path):
    out, content_types, slide_xml, rels_xml = _build_audio_pptx(tmp_path, "once")

    with zipfile.ZipFile(out) as z:
        assert "ppt/media/media1.wav" in z.namelist()
        poster_bytes = z.read("ppt/media/image1.png")
        poster = Image.open(z.open("ppt/media/image1.png"))
        assert poster.size == (598, 600)
        assert hashlib.sha1(poster_bytes).hexdigest() == hashlib.sha1(
            AUDIO_SPEAKER_ICON.read_bytes()
        ).hexdigest()
    assert 'ContentType="audio/x-wav"' in content_types
    assert "relationships/media" in rels_xml
    assert "relationships/audio" in rels_xml
    assert "relationships/video" not in rels_xml
    assert "<a:audioFile" in slide_xml
    assert "<a:videoFile" not in slide_xml
    assert "<p:audio>" in slide_xml
    assert "<p:video>" not in slide_xml
    assert "<p:cMediaNode" in slide_xml
    assert 'nodeType="mainSeq"' in slide_xml
    assert 'nodeType="clickEffect"' in slide_xml
    assert 'cmd="playFrom(0.0)"' in slide_xml
    assert '<p:cond delay="indefinite"' in slide_xml
    assert "repeatCount" not in slide_xml
    assert 'cx="640080"' in slide_xml
    assert 'cy="640080"' in slide_xml
    assert not re.search(r"<a:off x=\"-", slide_xml)
    assert len(Presentation(str(out)).slides) == 1


def test_loop_audio_sets_indefinite_repeat(tmp_path):
    _out, _content_types, slide_xml, _rels_xml = _build_audio_pptx(tmp_path, "loop")

    assert 'repeatCount="indefinite"' in slide_xml
    assert 'cmd="playFrom(0.0)"' in slide_xml


def test_auto_audio_starts_immediately(tmp_path):
    _out, _content_types, slide_xml, _rels_xml = _build_audio_pptx(
        tmp_path, "once", audio_trigger="auto"
    )

    assert '<p:cond delay="0"' in slide_xml
    assert 'nodeType="clickEffect"' not in slide_xml
    assert 'cmd="playFrom(0.0)"' not in slide_xml


def test_audio_validation_reports_missing_file(tmp_path):
    project = Project(sections=[MediaSection(audio_ref="media/missing.wav")])
    issues = validate_project(project, media_root=tmp_path / "work")

    assert issues
    assert issues[0]["level"] == "error"
    assert "音频文件不存在" in issues[0]["message"]


def test_export_blocks_unsupported_audio_format(tmp_path):
    work = tmp_path / "work"
    media = media_store.media_dir(work)
    (media / "song.m4a").write_bytes(b"not-real-audio")
    project = Project(sections=[MediaSection(audio_ref="media/song.m4a")])

    with pytest.raises(ExportError) as exc:
        export_project(project, tmp_path / "bad.pptx", media_root=work)

    assert "音频导出仅支持 mp3 / wav" in exc.value.message
