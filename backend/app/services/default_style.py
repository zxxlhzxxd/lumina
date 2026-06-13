"""Single built-in visual style used for every project."""
from __future__ import annotations

from app.domain.enums import SectionType
from app.domain.style import SectionStyle, TextStyle

CJK_FONT = "Microsoft YaHei"


def default_style() -> SectionStyle:
    return SectionStyle(
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
    )


def type_styles() -> dict[str, SectionStyle]:
    return {
        SectionType.HYMN.value: SectionStyle(
            body=TextStyle(
                font_family=CJK_FONT,
                font_size=40,
                color="#2B2B2B",
                bold=True,
                align="center",
            )
        ),
    }
