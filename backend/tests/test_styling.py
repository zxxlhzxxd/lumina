"""Tests for the built-in style cascade (§4.6)."""
from app.domain.sections import CoverSection, HymnSection
from app.domain.style import (
    BlockLayout,
    EdgeInsets,
    SectionStyle,
    TextBlockStyle,
    TextStyle,
)
from app.services.styling import _merge_style, resolve_style


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


def test_explicit_false_overrides_inherited_boolean_style():
    section = HymnSection(style=SectionStyle(body=TextStyle(bold=False)))
    resolved = resolve_style(section)
    assert resolved.body.bold is False


def test_extended_font_style_fields_survive_resolution():
    section = CoverSection(
        style=SectionStyle(
            title=TextStyle(
                italic=True,
                underline=True,
                highlight_color="#FFF200",
            )
        )
    )
    resolved = resolve_style(section)
    assert resolved.title.italic is True
    assert resolved.title.underline is True
    assert resolved.title.highlight_color == "#FFF200"


def test_block_layout_cascades_per_block_and_margin_side():
    base = SectionStyle(
        blocks={
            "body": TextBlockStyle(
                layout=BlockLayout(
                    anchor="middle_center",
                    margin=EdgeInsets(top=0.6, right=0.8, bottom=0.7, left=0.8),
                )
            ),
            "title": TextBlockStyle(
                layout=BlockLayout(anchor="top_center")
            ),
        }
    )
    override = SectionStyle(
        blocks={
            "body": TextBlockStyle(
                text=TextStyle(color="#ABCDEF", vertical_align="bottom"),
                layout=BlockLayout(
                    anchor="bottom_right",
                    margin=EdgeInsets(right=0.4),
                ),
            )
        }
    )
    merged = _merge_style(base, override)
    body = merged.blocks["body"]
    assert body.text.color == "#ABCDEF"
    assert body.text.vertical_align == "bottom"
    layout = body.layout
    assert layout.anchor == "bottom_right"
    assert layout.margin.top == 0.6
    assert layout.margin.right == 0.4
    assert layout.margin.bottom == 0.7
    assert merged.blocks["title"].layout.anchor == "top_center"
