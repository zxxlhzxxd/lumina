"""Built-in visual themes (read-only).

Each theme provides a global default style plus a couple of per-section-type
overrides. Users duplicate a built-in theme to create an editable copy.
"""
from __future__ import annotations

from typing import List

from app.domain.enums import SectionType
from app.domain.project import Theme
from app.domain.style import SectionStyle, TextStyle

CJK_FONT = "Microsoft YaHei"


def _dark_theme() -> Theme:
    return Theme(
        id="builtin-night",
        name="夜祷（暗色）",
        builtin=True,
        default_style=SectionStyle(
            background_color="#0D1B2A",
            body=TextStyle(
                font_family=CJK_FONT, font_size=32, color="#F5F5F5", align="center"
            ),
            title=TextStyle(
                font_family=CJK_FONT,
                font_size=54,
                color="#F5F5F5",
                bold=True,
                align="center",
            ),
            label=TextStyle(font_family=CJK_FONT, font_size=44, color="#E0B34A", bold=True),
            margin=0.8,
        ),
        type_styles={
            SectionType.HYMN.value: SectionStyle(
                body=TextStyle(
                    font_family=CJK_FONT,
                    font_size=40,
                    color="#F5F5F5",
                    bold=True,
                    align="center",
                )
            ),
            SectionType.RESPONSIVE_READING.value: SectionStyle(
                body=TextStyle(
                    font_family=CJK_FONT,
                    font_size=40,
                    color="#F5F5F5",
                    bold=True,
                    align="center",
                )
            ),
        },
    )


def _light_theme() -> Theme:
    return Theme(
        id="builtin-dawn",
        name="晨曦（浅色）",
        builtin=True,
        default_style=SectionStyle(
            background_color="#F7F3E9",
            body=TextStyle(
                font_family=CJK_FONT, font_size=32, color="#2B2B2B", align="center"
            ),
            title=TextStyle(
                font_family=CJK_FONT,
                font_size=54,
                color="#7A5C1E",
                bold=True,
                align="center",
            ),
            label=TextStyle(font_family=CJK_FONT, font_size=44, color="#B8860B", bold=True),
            margin=0.8,
        ),
        type_styles={
            SectionType.HYMN.value: SectionStyle(
                body=TextStyle(
                    font_family=CJK_FONT,
                    font_size=40,
                    color="#2B2B2B",
                    bold=True,
                    align="center",
                )
            ),
        },
    )


def builtin_themes() -> List[Theme]:
    return [_dark_theme(), _light_theme()]


def default_theme_id() -> str:
    return "builtin-night"
