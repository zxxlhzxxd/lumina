"""Text block specifications and relative placement resolution."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from app.services.generation import SlideModel

DEFAULT_MARGIN_IN = 0.8
MIN_BOX_IN = 0.01


@dataclass(frozen=True)
class Rect:
    left: float
    top: float
    width: float
    height: float


@dataclass(frozen=True)
class TextBlockSpec:
    block_id: str
    role: str
    text: str
    rect: Rect
    default_anchor: str
    size: float
    rich_text: Optional[list[list[dict]]] = None
    bold: bool = False
    color: str = "#F5F5F5"
    align: str = "center"
    vertical_anchor: str = "middle"


def _legacy_margin(style: Optional[dict]) -> float:
    value = (style or {}).get("margin")
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return DEFAULT_MARGIN_IN


def _block_override(style: Optional[dict], block_id: str) -> Optional[dict]:
    blocks = (style or {}).get("blocks")
    if not isinstance(blocks, dict):
        return None
    block = blocks.get(block_id)
    if not isinstance(block, dict):
        return None
    value = block.get("layout")
    return value if isinstance(value, dict) else None


def _fit_margins(start: float, end: float, total: float) -> tuple[float, float]:
    start = max(0.0, start)
    end = max(0.0, end)
    maximum = max(0.0, total - MIN_BOX_IN)
    combined = start + end
    if combined <= maximum or combined == 0:
        return start, end
    scale = maximum / combined
    return start * scale, end * scale


def resolve_block_rect(
    base: Rect,
    *,
    block_id: str,
    default_anchor: str,
    style: Optional[dict],
    slide_width: float,
    slide_height: float,
) -> Rect:
    """Resolve a configured block while preserving legacy rectangles by default."""
    override = _block_override(style, block_id)
    if override is None:
        return base

    fallback = _legacy_margin(style)
    margin = override.get("margin")
    margin = margin if isinstance(margin, dict) else {}
    top = float(margin.get("top", fallback))
    right = float(margin.get("right", fallback))
    bottom = float(margin.get("bottom", fallback))
    left = float(margin.get("left", fallback))
    left, right = _fit_margins(left, right, slide_width)
    top, bottom = _fit_margins(top, bottom, slide_height)

    available_width = max(MIN_BOX_IN, slide_width - left - right)
    available_height = max(MIN_BOX_IN, slide_height - top - bottom)
    width = min(base.width, available_width)
    height = min(base.height, available_height)

    anchor = override.get("anchor") or default_anchor
    vertical, horizontal = anchor.split("_", 1)
    if horizontal == "left":
        resolved_left = left
    elif horizontal == "right":
        resolved_left = slide_width - right - width
    else:
        resolved_left = left + (available_width - width) / 2

    if vertical == "top":
        resolved_top = top
    elif vertical == "bottom":
        resolved_top = slide_height - bottom - height
    else:
        resolved_top = top + (available_height - height) / 2

    return Rect(resolved_left, resolved_top, width, height)


def slide_text_blocks(
    sm: SlideModel, slide_width: float, slide_height: float
) -> list[TextBlockSpec]:
    """Return all text blocks for a slide using legacy dimensions as defaults."""
    margin = _legacy_margin(sm.style)
    content_width = max(MIN_BOX_IN, slide_width - 2 * margin)
    blocks: list[TextBlockSpec] = []

    if sm.kind in ("cover", "scripture_title", "hymn_title"):
        blocks.append(
            TextBlockSpec(
                "title",
                "title",
                sm.title or "",
                Rect(margin, 2.4, content_width, 2.0),
                "middle_center",
                54,
                bold=True,
            )
        )
        if sm.subtitle:
            blocks.append(
                TextBlockSpec(
                    "subtitle",
                    "body",
                    sm.subtitle,
                    Rect(margin, 4.5, content_width, 1.2),
                    "bottom_center",
                    28,
                    color="#9FB3C8",
                )
            )
        if sm.body:
            blocks.append(
                TextBlockSpec(
                    "extra",
                    "body",
                    sm.body,
                    Rect(margin, 5.7, content_width, 1.0),
                    "bottom_center",
                    22,
                    color="#9FB3C8",
                )
            )
    elif sm.kind == "responsive_verse":
        if sm.label:
            blocks.append(
                TextBlockSpec(
                    "label",
                    "label",
                    sm.label,
                    Rect(margin, 0.5, 1.4, 1.4),
                    "top_left",
                    44,
                    bold=True,
                    color="#E0B34A",
                    align="left",
                    vertical_anchor="top",
                )
            )
        blocks.append(
            TextBlockSpec(
                "body",
                "body",
                sm.body or "",
                Rect(margin, 1.6, content_width, 4.6),
                "middle_center",
                40,
                bold=True,
            )
        )
        if sm.reference:
            blocks.append(
                TextBlockSpec(
                    "reference",
                    "body",
                    sm.reference,
                    Rect(margin, 6.5, content_width, 0.7),
                    "bottom_center",
                    20,
                    color="#9FB3C8",
                    vertical_anchor="bottom",
                )
            )
    else:
        body_top = 0.8
        if sm.title:
            blocks.append(
                TextBlockSpec(
                    "title",
                    "title",
                    sm.title,
                    Rect(margin, 0.6, content_width, 1.1),
                    "top_center",
                    36,
                    bold=True,
                    color="#E0B34A",
                    vertical_anchor="top",
                )
            )
            body_top = 1.9
        body_height = max(MIN_BOX_IN, slide_height - body_top - 0.9)
        blocks.append(
            TextBlockSpec(
                "body",
                "body",
                sm.body or "",
                Rect(margin, body_top, content_width, body_height),
                "middle_center",
                40 if sm.section_type == "hymn" else 32,
                rich_text=sm.rich_body,
                bold=sm.section_type == "hymn",
            )
        )
        if sm.reference:
            blocks.append(
                TextBlockSpec(
                    "reference",
                    "body",
                    sm.reference,
                    Rect(margin, slide_height - 0.8, content_width, 0.6),
                    "bottom_center",
                    18,
                    color="#9FB3C8",
                    vertical_anchor="bottom",
                )
            )

    return [
        replace(
            block,
            rect=resolve_block_rect(
                block.rect,
                block_id=block.block_id,
                default_anchor=block.default_anchor,
                style=sm.style,
                slide_width=slide_width,
                slide_height=slide_height,
            ),
        )
        for block in blocks
    ]
