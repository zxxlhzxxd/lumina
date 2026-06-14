"""PPTX rendering engine.

Renders a list of `SlideModel` (produced by `services.generation`) into a
PowerPoint file using python-pptx. Each slide carries a resolved (cascaded)
style; the builder honours background color/image, fonts, sizes, colors and
alignment, falling back to a projection-friendly dark default when unset.

Background images are embedded (§6.4.1). Media slides can embed mp3/wav audio
and place it in the slide click sequence (§6.4.2). Video remains a later phase.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import PartFactory
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.parts.media import MediaPart
from pptx.util import Emu, Inches, Pt

from app.core.errors import ExportError
from app.domain.enums import SlideSize
from app.services import media_store
from app.services.generation import SlideModel

# Projection-friendly fallback palette (used when a style field is unset).
BG_COLOR = RGBColor(0x0D, 0x1B, 0x2A)
TEXT_COLOR = RGBColor(0xF5, 0xF5, 0xF5)
ACCENT_COLOR = RGBColor(0xE0, 0xB3, 0x4A)
MUTED_COLOR = RGBColor(0x9F, 0xB3, 0xC8)

CJK_FONT = "Microsoft YaHei"

_ALIGN = {
    "left": PP_ALIGN.LEFT,
    "center": PP_ALIGN.CENTER,
    "right": PP_ALIGN.RIGHT,
}

_SIZE_EMU = {
    SlideSize.WIDE: (Inches(13.333), Inches(7.5)),
    SlideSize.STANDARD: (Inches(10), Inches(7.5)),
}

AUDIO_MIME_BY_EXT = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/x-wav",
}

AUDIO_SPEAKER_ICON = Path(__file__).parent / "assets" / "audio-speaker-icon.png"


def _register_audio_media_parts() -> None:
    """Teach python-pptx how to reopen generated audio MediaPart entries."""
    for content_type in ("audio/mp3", "audio/mpeg", "audio/x-wav", "audio/wav"):
        PartFactory.part_type_for[content_type] = MediaPart


_register_audio_media_parts()


def _speaker_icon_png() -> io.BytesIO:
    """Return the bundled PowerPoint-style speaker poster frame."""
    return io.BytesIO(AUDIO_SPEAKER_ICON.read_bytes())


def _hex_to_rgb(value: Optional[str]) -> Optional[RGBColor]:
    if not value:
        return None
    v = value.lstrip("#")
    if len(v) != 6:
        return None
    try:
        return RGBColor(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    except ValueError:
        return None


def _role(style: Optional[dict], role: str) -> dict:
    if not style:
        return {}
    return style.get(role) or {}


def _set_font(run, *, size: float, bold: bool, color: RGBColor, font: str) -> None:
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = rpr.makeelement(qn(tag), {})
            rpr.append(el)
        el.set("typeface", font)


class PptxBuilder:
    def __init__(
        self,
        slide_size: SlideSize = SlideSize.WIDE,
        media_root: Optional[Path] = None,
    ) -> None:
        self.prs = Presentation()
        w, h = _SIZE_EMU.get(slide_size, _SIZE_EMU[SlideSize.WIDE])
        self.prs.slide_width = w
        self.prs.slide_height = h
        self.width = w
        self.height = h
        self.media_root = media_root
        self._blank = self.prs.slide_layouts[6]

    # ---- media -----------------------------------------------------------
    def _audio_path(self, ref: str) -> Path:
        if self.media_root is None:
            raise ExportError("导出音频需要工程媒体目录")
        path = media_store.media_path(self.media_root, ref)
        if path is None or not path.exists():
            raise ExportError(f"音频文件不存在: {ref}")
        if path.suffix.lower() not in AUDIO_MIME_BY_EXT:
            raise ExportError(f"不支持的音频格式: {path.suffix or '未知'}")
        return path

    def _embed_audio(self, slide, sm: SlideModel) -> None:
        ref = sm.audio_ref
        if not ref:
            return
        audio_path = self._audio_path(ref)
        mime_type = AUDIO_MIME_BY_EXT[audio_path.suffix.lower()]
        shape = slide.shapes.add_movie(
            str(audio_path),
            left=Emu(self.width - Inches(1.15)),
            top=Emu(self.height - Inches(1.05)),
            width=Inches(0.7),
            height=Inches(0.7),
            poster_frame_image=_speaker_icon_png(),
            mime_type=mime_type,
        )
        self._convert_movie_shape_to_audio(slide, shape)
        self._set_audio_timing(
            slide,
            shape.shape_id,
            loop=sm.play_mode == "loop",
            auto=sm.audio_trigger == "auto",
        )

    def _convert_movie_shape_to_audio(self, slide, shape) -> None:
        video_file = shape._element.find(".//" + qn("a:videoFile"))
        if video_file is None:
            raise ExportError("生成 PPTX 音频对象失败")
        video_rid = video_file.get(qn("r:link"))
        if not video_rid:
            raise ExportError("生成 PPTX 音频对象失败")
        media_part = slide.part.related_part(video_rid)
        audio_rid = slide.part.relate_to(media_part, RT.AUDIO)
        video_file.tag = qn("a:audioFile")
        video_file.set(qn("r:link"), audio_rid)
        slide.part.drop_rel(video_rid)

    def _set_audio_timing(
        self,
        slide,
        shape_id: int,
        *,
        loop: bool,
        auto: bool,
    ) -> None:
        timing_xml = (
            self._auto_audio_timing_xml(shape_id, loop)
            if auto
            else self._click_audio_timing_xml(shape_id, loop)
        )
        timing = parse_xml(timing_xml)
        old_timing = slide._element.find(qn("p:timing"))
        if old_timing is None:
            slide._element.append(timing)
            return
        parent = old_timing.getparent()
        parent.insert(parent.index(old_timing), timing)
        parent.remove(old_timing)

    def _auto_audio_timing_xml(self, shape_id: int, loop: bool) -> str:
        repeat = ' repeatCount="indefinite"' if loop else ""
        return (
            '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            "<p:tnLst><p:par>"
            '<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
            "<p:childTnLst><p:audio><p:cMediaNode vol=\"80000\">"
            f'<p:cTn id="2" fill="hold" display="0"{repeat}>'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            '<p:endCondLst><p:cond evt="onStopAudio" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:endCondLst>'
            "</p:cTn>"
            f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
            "</p:cMediaNode></p:audio></p:childTnLst>"
            "</p:cTn></p:par></p:tnLst></p:timing>"
        )

    def _click_audio_timing_xml(self, shape_id: int, loop: bool) -> str:
        repeat = ' repeatCount="indefinite"' if loop else ""
        return (
            '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            "<p:tnLst><p:par>"
            '<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
            '<p:childTnLst><p:seq concurrent="1" nextAc="seek">'
            '<p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
            "<p:childTnLst><p:par><p:cTn id=\"3\" fill=\"hold\">"
            '<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
            '<p:childTnLst><p:par><p:cTn id="4" fill="hold">'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            '<p:childTnLst><p:par><p:cTn id="5" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="clickEffect">'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            '<p:childTnLst><p:cmd type="call" cmd="playFrom(0.0)">'
            '<p:cBhvr><p:cTn id="6" dur="1000" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
            "</p:cBhvr></p:cmd></p:childTnLst></p:cTn></p:par>"
            "</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>"
            "</p:childTnLst></p:cTn>"
            '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
            "</p:seq>"
            "<p:audio><p:cMediaNode vol=\"80000\">"
            f'<p:cTn id="7" fill="hold" display="0"{repeat}>'
            '<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
            '<p:endCondLst><p:cond evt="onStopAudio" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:endCondLst>'
            "</p:cTn>"
            f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
            "</p:cMediaNode></p:audio></p:childTnLst>"
            "</p:cTn></p:par></p:tnLst></p:timing>"
        )

    # ---- slide scaffolding ----------------------------------------------
    def _new_slide(self, sm: SlideModel):
        slide = self.prs.slides.add_slide(self._blank)
        style = sm.style or {}
        bg_color = _hex_to_rgb(style.get("background_color")) or BG_COLOR
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = bg_color
        # Background image (covers the whole slide, added behind the text).
        bg_image = style.get("background_image")
        if bg_image and self.media_root is not None:
            try:
                path = media_store.media_path(self.media_root, bg_image)
            except Exception:  # noqa: BLE001
                path = None
            if path is not None and path.exists():
                slide.shapes.add_picture(
                    str(path), 0, 0, width=self.width, height=self.height
                )
        return slide

    def _margin(self, sm: SlideModel) -> Emu:
        margin_in = (sm.style or {}).get("margin")
        if isinstance(margin_in, (int, float)) and margin_in > 0:
            return Inches(float(margin_in))
        return Inches(0.8)

    def _content_box(self, sm: SlideModel):
        mx = self._margin(sm)
        return mx, Emu(self.width - 2 * mx)

    def _add_text(
        self,
        slide,
        text: str,
        sm: SlideModel,
        role: str,
        *,
        left: Emu,
        top: Emu,
        width: Emu,
        height: Emu,
        size: float,
        bold: bool = False,
        color: RGBColor = TEXT_COLOR,
        align: PP_ALIGN = PP_ALIGN.CENTER,
        anchor: MSO_ANCHOR = MSO_ANCHOR.MIDDLE,
        line_spacing: float = 1.15,
    ):
        ts = _role(sm.style, role)
        size = ts.get("font_size") or size
        bold = ts.get("bold") if ts.get("bold") is not None else bold
        color = _hex_to_rgb(ts.get("color")) or color
        font = ts.get("font_family") or CJK_FONT
        align = _ALIGN.get(ts.get("align"), align)
        line_spacing = ts.get("line_spacing") or line_spacing

        box = slide.shapes.add_textbox(left, top, width, height)
        tf = box.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        lines = text.split("\n") if text else [""]
        for i, line in enumerate(lines):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.alignment = align
            para.line_spacing = line_spacing
            run = para.add_run()
            run.text = line
            _set_font(run, size=size, bold=bool(bold), color=color, font=font)
        return box

    # ---- rendering -------------------------------------------------------
    def render(self, slides: List[SlideModel]) -> None:
        for sm in slides:
            self._render_slide(sm)
        if not self.prs.slides._sldIdLst.findall(qn("p:sldId")):
            self._render_slide(
                SlideModel(kind="blank", section_id="", section_type="")
            )

    def _render_slide(self, sm: SlideModel) -> None:
        kind = sm.kind
        if kind in ("cover", "scripture_title", "hymn_title"):
            self._render_title(sm)
        elif kind == "responsive_verse":
            self._render_responsive(sm)
        else:
            self._render_body(sm)

    def _render_title(self, sm: SlideModel) -> None:
        slide = self._new_slide(sm)
        mx, content_w = self._content_box(sm)
        self._add_text(
            slide, sm.title or "", sm, "title",
            left=mx, top=Inches(2.4), width=content_w, height=Inches(2.0),
            size=54, bold=True,
        )
        if sm.subtitle:
            self._add_text(
                slide, sm.subtitle, sm, "body",
                left=mx, top=Inches(4.5), width=content_w, height=Inches(1.2),
                size=28, color=MUTED_COLOR,
            )
        if sm.body:
            self._add_text(
                slide, sm.body, sm, "body",
                left=mx, top=Inches(5.7), width=content_w, height=Inches(1.0),
                size=22, color=MUTED_COLOR,
            )

    def _render_responsive(self, sm: SlideModel) -> None:
        slide = self._new_slide(sm)
        mx, content_w = self._content_box(sm)
        if sm.label:
            self._add_text(
                slide, sm.label, sm, "label",
                left=mx, top=Inches(0.5), width=Inches(1.4), height=Inches(1.4),
                size=44, bold=True, color=ACCENT_COLOR,
                align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
            )
        self._add_text(
            slide, sm.body or "", sm, "body",
            left=mx, top=Inches(1.6), width=content_w, height=Inches(4.6),
            size=40, bold=True,
        )
        if sm.reference:
            self._add_text(
                slide, sm.reference, sm, "body",
                left=mx, top=Inches(6.5), width=content_w, height=Inches(0.7),
                size=20, color=MUTED_COLOR, anchor=MSO_ANCHOR.BOTTOM,
            )

    def _render_body(self, sm: SlideModel) -> None:
        slide = self._new_slide(sm)
        mx, content_w = self._content_box(sm)
        top = Inches(0.8)
        if sm.title:
            self._add_text(
                slide, sm.title, sm, "title",
                left=mx, top=Inches(0.6), width=content_w, height=Inches(1.1),
                size=36, bold=True, color=ACCENT_COLOR, anchor=MSO_ANCHOR.TOP,
            )
            top = Inches(1.9)
        body_h = Emu(self.height - top - Inches(0.9))
        size = 40 if sm.section_type == "hymn" else 32
        self._add_text(
            slide, sm.body or "", sm, "body",
            left=mx, top=top, width=content_w, height=body_h,
            size=size, bold=sm.section_type == "hymn",
        )
        if sm.reference:
            self._add_text(
                slide, sm.reference, sm, "body",
                left=mx, top=Emu(self.height - Inches(0.8)),
                width=content_w, height=Inches(0.6),
                size=18, color=MUTED_COLOR, anchor=MSO_ANCHOR.BOTTOM,
            )
        self._embed_audio(slide, sm)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(path))
        return path


def build_pptx(
    slides: List[SlideModel],
    path: Path,
    slide_size: SlideSize = SlideSize.WIDE,
    media_root: Optional[Path] = None,
) -> Path:
    builder = PptxBuilder(slide_size, media_root=media_root)
    builder.render(slides)
    return builder.save(path)
