"""Punctuation-only display strategy.

Replaces CJK corner quotes with contemporary quotation marks. The mapping
contains punctuation code points only; wording, names, and 　神 spacing are
untouched.
"""

from __future__ import annotations

from typing import Mapping, Optional

# Source keys and values are all punctuation. Do not add letters or words.
CONTEMPORARY_QUOTE_MAP: Mapping[str, str] = {
    "「": "“",
    "」": "”",
    "『": "‘",
    "』": "’",
    "﹁": "“",
    "﹂": "”",
    "﹃": "‘",
    "﹄": "’",
}


class PunctuationTransform:
    """1:1 punctuation code-point replacement. No pairing, no word edits."""

    name = "punctuation"

    def __init__(self, mapping: Optional[Mapping[str, str]] = None) -> None:
        table = mapping if mapping is not None else CONTEMPORARY_QUOTE_MAP
        self._table = str.maketrans(dict(table))

    def apply(self, text: str) -> str:
        return text.translate(self._table)
