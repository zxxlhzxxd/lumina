"""Tests for the three-level style cascade (§4.6)."""
from app.domain.project import Theme
from app.domain.sections import CoverSection, HymnSection
from app.domain.style import SectionStyle, TextStyle
from app.services.styling import resolve_style


def _theme() -> Theme:
    return Theme(
        default_style=SectionStyle(
            background_color="#000000",
            body=TextStyle(font_size=10, color="#FFFFFF"),
        ),
        type_styles={
            "hymn": SectionStyle(body=TextStyle(font_size=20)),
        },
    )


def test_cascade_type_overrides_default():
    section = HymnSection()
    resolved = resolve_style(_theme(), section)
    assert resolved.background_color == "#000000"  # from default
    assert resolved.body.font_size == 20  # type override
    assert resolved.body.color == "#FFFFFF"  # inherited from default


def test_section_override_wins():
    section = HymnSection(style=SectionStyle(body=TextStyle(color="#ABCDEF")))
    resolved = resolve_style(_theme(), section)
    assert resolved.body.color == "#ABCDEF"  # section override
    assert resolved.body.font_size == 20  # still from type level


def test_no_type_style_falls_back_to_default():
    section = CoverSection()
    resolved = resolve_style(_theme(), section)
    assert resolved.body.font_size == 10  # default, no cover type style


def test_no_theme_returns_section_only():
    section = HymnSection(style=SectionStyle(background_color="#123456"))
    resolved = resolve_style(None, section)
    assert resolved.background_color == "#123456"
    assert resolved.body is None or resolved.body.font_size is None
    assert resolved.title is None or resolved.title.font_size is None
