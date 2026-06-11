"""Style cascade resolution (§4.6).

Effective style = Theme.default_style -> Theme.type_styles[type] -> Section.style,
merged "nearest wins". Unset fields fall through to the level above.
"""
from __future__ import annotations

from typing import Optional

from app.domain.project import Theme
from app.domain.sections import Section
from app.domain.style import SectionStyle, TextStyle


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
    return base


def resolve_style(theme: Optional[Theme], section: Section) -> SectionStyle:
    """Compute the effective, fully cascaded style for a section."""
    effective = SectionStyle()
    if theme is not None:
        effective = _merge_style(effective, theme.default_style)
        type_style = theme.type_styles.get(section.type.value)
        effective = _merge_style(effective, type_style)
    effective = _merge_style(effective, getattr(section, "style", None))
    return effective
