"""Style cascade resolution (§4.6).

Effective style = built-in default -> per-type default -> Section.style,
merged "nearest wins". Unset fields fall through to the level above.
"""
from __future__ import annotations

from typing import Optional

from app.domain.sections import Section
from app.domain.style import (
    BlockLayout,
    EdgeInsets,
    SectionStyle,
    TextBlockStyle,
    TextStyle,
)
from app.services.default_style import default_style, type_styles


def _merge_text(base: Optional[TextStyle], over: Optional[TextStyle]) -> Optional[TextStyle]:
    if base is None:
        return over.model_copy(deep=True) if over else None
    if over is None:
        return base.model_copy(deep=True)
    merged = base.model_dump()
    for key, value in over.model_dump().items():
        if value is not None:
            merged[key] = value
    return TextStyle(**merged)


def _merge_insets(
    base: Optional[EdgeInsets], over: Optional[EdgeInsets]
) -> Optional[EdgeInsets]:
    if base is None:
        return over.model_copy(deep=True) if over else None
    if over is None:
        return base.model_copy(deep=True)
    merged = base.model_dump()
    for key, value in over.model_dump().items():
        if value is not None:
            merged[key] = value
    return EdgeInsets(**merged)


def _merge_block(
    base: Optional[BlockLayout], over: Optional[BlockLayout]
) -> Optional[BlockLayout]:
    if base is None:
        return over.model_copy(deep=True) if over else None
    if over is None:
        return base.model_copy(deep=True)
    return BlockLayout(
        anchor=over.anchor if over.anchor is not None else base.anchor,
        margin=_merge_insets(base.margin, over.margin),
    )


def _merge_text_block(
    base: Optional[TextBlockStyle], over: Optional[TextBlockStyle]
) -> Optional[TextBlockStyle]:
    if base is None:
        return over.model_copy(deep=True) if over else None
    if over is None:
        return base.model_copy(deep=True)
    return TextBlockStyle(
        text=_merge_text(base.text, over.text),
        layout=_merge_block(base.layout, over.layout),
    )


def _merge_style(base: Optional[SectionStyle], over: Optional[SectionStyle]) -> SectionStyle:
    base = base.model_copy(deep=True) if base else SectionStyle()
    if over is None:
        return base
    for attr in ("background_color", "background_image", "background_video", "margin"):
        value = getattr(over, attr, None)
        if value is not None:
            setattr(base, attr, value)
    base.body = _merge_text(base.body, over.body)
    base.title = _merge_text(base.title, over.title)
    base.label = _merge_text(base.label, over.label)
    blocks = {key: value.model_copy(deep=True) for key, value in base.blocks.items()}
    for key, value in over.blocks.items():
        merged = _merge_text_block(blocks.get(key), value)
        if merged is not None:
            blocks[key] = merged
    base.blocks = blocks
    return base


def resolve_style(section: Section) -> SectionStyle:
    """Compute the effective, fully cascaded style for a section."""
    effective = _merge_style(SectionStyle(), default_style())
    type_style = type_styles().get(section.type.value)
    effective = _merge_style(effective, type_style)
    effective = _merge_style(effective, getattr(section, "style", None))
    return effective
