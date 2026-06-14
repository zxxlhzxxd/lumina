"""Built-in liturgy texts (使徒信经 / 主祷文 / 荣耀颂 etc.).

Standard simplified-Chinese liturgical texts in the public domain. Used both to
seed the liturgy library and (via stable ids) by the default service template.
"""
from __future__ import annotations

from typing import List

from app.domain.library import LiturgyText

APOSTLES_CREED: List[str] = [
    "我信上帝，全能的父，创造天地的主。",
    "我信我主耶稣基督，上帝独生的子；因圣灵感孕，由童贞女马利亚所生；"
    "在本丢彼拉多手下受难，被钉于十字架，受死，埋葬；降在阴间；"
    "第三天从死里复活；后升天，坐在全能父上帝的右边；"
    "将来必从那里降临，审判活人死人。",
    "我信圣灵；我信圣而公之教会；我信圣徒相通；我信罪得赦免；"
    "我信身体复活；我信永生。阿们。",
]

LORDS_PRAYER: List[str] = [
    "我们在天上的父：愿人都尊你的名为圣。愿你的国降临；"
    "愿你的旨意行在地上，如同行在天上。",
    "我们日用的饮食，今日赐给我们。免我们的债，如同我们免了人的债。"
    "不叫我们遇见试探；救我们脱离凶恶。",
    "因为国度、权柄、荣耀，全是你的，直到永远。阿们。",
]

GLORIA: List[str] = [
    "愿荣耀归于父、子、圣灵；起初这样，现在这样，以后也这样，永无穷尽。阿们。",
]


def builtin_liturgy_texts() -> List[LiturgyText]:
    return [
        LiturgyText(
            id="builtin-apostles-creed",
            title="使徒信经",
            builtin=True,
            paragraphs=list(APOSTLES_CREED),
        ),
        LiturgyText(
            id="builtin-lords-prayer",
            title="主祷文",
            builtin=True,
            paragraphs=list(LORDS_PRAYER),
        ),
        LiturgyText(
            id="builtin-gloria",
            title="荣耀颂",
            builtin=True,
            paragraphs=list(GLORIA),
        ),
    ]
