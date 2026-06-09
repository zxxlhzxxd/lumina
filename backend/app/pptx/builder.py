"""PPTX rendering engine.

Renders a list of `SlideModel` (produced by `services.generation`) into a
PowerPoint file using python-pptx. Phase 1 renders cover / responsive_reading /
scripture / liturgy_text fully; other kinds get a reasonable generic layout.

The visual style is a fixed, projection-friendly dark theme for phase 1. The
Theme system (configurable per project) is a phase-2 concern.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from app.domain.enums import SlideSize
from app.services.generation import SlideModel

# Projection-friendly palette.
BG_COLOR = RGBColor(0x0D, 0x1B, 0x2A)
TEXT_COLOR = RGBColor(0xF5, 0xF5, 0xF5)
ACCENT_COLOR = RGBColor(0xE0, 0xB3, 0x4A)  # 启/应 label + accents
MUTED_COLOR = RGBColor(0x9F, 0xB3, 0xC8)

CJK_FONT = "Microsoft YaHei"  # PowerPoint substitutes if unavailable

_SIZE_EMU = {
    SlideSize.WIDE: (Inches(13.333), Inches(7.5)),
    SlideSize.STANDARD: (Inches(10), Inches(7.5)),
}


def _set_font(run, *, size: float, bold: bool, color: RGBColor, font: str = CJK_FONT) -> None:
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    # Ensure East Asian text uses the same font (python-pptx only sets latin).
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = rpr.makeelement(qn(tag), {})
            rpr.append(el)
        el.set("typeface", font)


def _add_text(
    slide,
    text: str,
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
        _set_font(run, size=size, bold=bold, color=color)
    return box


class PptxBuilder:
    def __init__(self, slide_size: SlideSize = SlideSize.WIDE) -> None:
        self.prs = Presentation()
        w, h = _SIZE_EMU.get(slide_size, _SIZE_EMU[SlideSize.WIDE])
        self.prs.slide_width = w
        self.prs.slide_height = h
        self.width = w
        self.height = h
        self._blank = self.prs.slide_layouts[6]

    def _new_slide(self):
        slide = self.prs.slides.add_slide(self._blank)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = BG_COLOR
        return slide

    def _margins(self):
        mx = Inches(0.8)
        return mx, Emu(self.width - 2 * mx)

    def render(self, slides: List[SlideModel]) -> None:
        for sm in slides:
            self._render_slide(sm)
        if not self.prs.slides._sldIdLst.findall(qn("p:sldId")):
            # Never produce an empty deck — add a placeholder slide.
            self._new_slide()

    def _render_slide(self, sm: SlideModel) -> None:
        kind = sm.kind
        if kind in ("cover", "scripture_title", "hymn_title"):
            self._render_title(sm)
        elif kind == "responsive_verse":
            self._render_responsive(sm)
        else:
            self._render_body(sm)

    def _render_title(self, sm: SlideModel) -> None:
        slide = self._new_slide()
        mx, content_w = self._margins()
        _add_text(
            slide,
            sm.title or "",
            left=mx,
            top=Inches(2.4),
            width=content_w,
            height=Inches(2.0),
            size=54,
            bold=True,
        )
        if sm.subtitle:
            _add_text(
                slide,
                sm.subtitle,
                left=mx,
                top=Inches(4.5),
                width=content_w,
                height=Inches(1.2),
                size=28,
                color=MUTED_COLOR,
            )
        if sm.body:
            _add_text(
                slide,
                sm.body,
                left=mx,
                top=Inches(5.7),
                width=content_w,
                height=Inches(1.0),
                size=22,
                color=MUTED_COLOR,
            )

    def _render_responsive(self, sm: SlideModel) -> None:
        slide = self._new_slide()
        mx, content_w = self._margins()
        if sm.label:
            _add_text(
                slide,
                sm.label,
                left=mx,
                top=Inches(0.5),
                width=Inches(1.4),
                height=Inches(1.4),
                size=44,
                bold=True,
                color=ACCENT_COLOR,
                align=PP_ALIGN.LEFT,
                anchor=MSO_ANCHOR.TOP,
            )
        _add_text(
            slide,
            sm.body or "",
            left=mx,
            top=Inches(1.6),
            width=content_w,
            height=Inches(4.6),
            size=40,
            bold=True,
        )
        if sm.reference:
            _add_text(
                slide,
                sm.reference,
                left=mx,
                top=Inches(6.5),
                width=content_w,
                height=Inches(0.7),
                size=20,
                color=MUTED_COLOR,
                anchor=MSO_ANCHOR.BOTTOM,
            )

    def _render_body(self, sm: SlideModel) -> None:
        slide = self._new_slide()
        mx, content_w = self._margins()
        top = Inches(0.8)
        if sm.title:
            _add_text(
                slide,
                sm.title,
                left=mx,
                top=Inches(0.6),
                width=content_w,
                height=Inches(1.1),
                size=36,
                bold=True,
                color=ACCENT_COLOR,
                anchor=MSO_ANCHOR.TOP,
            )
            top = Inches(1.9)
        body_h = Emu(self.height - top - Inches(0.9))
        # Lyric pages use larger text for congregational reading.
        size = 40 if sm.section_type == "hymn" else 32
        _add_text(
            slide,
            sm.body or "",
            left=mx,
            top=top,
            width=content_w,
            height=body_h,
            size=size,
            bold=sm.section_type == "hymn",
        )
        if sm.reference:
            _add_text(
                slide,
                sm.reference,
                left=mx,
                top=Emu(self.height - Inches(0.8)),
                width=content_w,
                height=Inches(0.6),
                size=18,
                color=MUTED_COLOR,
                anchor=MSO_ANCHOR.BOTTOM,
            )

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(path))
        return path


def build_pptx(slides: List[SlideModel], path: Path, slide_size: SlideSize = SlideSize.WIDE) -> Path:
    builder = PptxBuilder(slide_size)
    builder.render(slides)
    return builder.save(path)
