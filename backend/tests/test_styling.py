"""Tests for the built-in style cascade (§4.6)."""
from app.domain.sections import CoverSection, HymnSection
from app.domain.style import SectionStyle, TextStyle
from app.services.styling import resolve_style


def test_type_style_overrides_default():
    section = HymnSection()
    resolved = resolve_style(section)
    assert resolved.background_color == "#F7F3E9"  # from default
    assert resolved.body.font_size == 40  # type override
    assert resolved.body.color == "#2B2B2B"  # inherited from default/type


def test_section_override_wins():
    section = HymnSection(style=SectionStyle(body=TextStyle(color="#ABCDEF")))
    resolved = resolve_style(section)
    assert resolved.body.color == "#ABCDEF"  # section override
    assert resolved.body.font_size == 40  # still from type level


def test_no_type_style_falls_back_to_default():
    section = CoverSection()
    resolved = resolve_style(section)
    assert resolved.body.font_size == 32  # default, no cover type style


def test_section_background_override_wins():
    section = HymnSection(style=SectionStyle(background_color="#123456"))
    resolved = resolve_style(section)
    assert resolved.background_color == "#123456"
