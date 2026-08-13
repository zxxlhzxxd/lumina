"""Remove the typesetting space that 神-edition texts place before 神."""

from __future__ import annotations

# 神版用一个空格把「神」撑成与「上帝」同宽。展示时去掉，不改用字。
_IDEOGRAPHIC_SPACE_SHEN = "\u3000神"
_ASCII_SPACE_SHEN = " 神"


class ShenSpacingTransform:
    """Strip a single space immediately before 神. No other wording changes."""

    name = "shen_spacing"

    def apply(self, text: str) -> str:
        return text.replace(_IDEOGRAPHIC_SPACE_SHEN, "神").replace(
            _ASCII_SPACE_SHEN, "神"
        )
