"""Default hymn examples (public-domain text and traditional translations).

Only hymns whose original text is in the public domain are listed here, using
widely-circulated traditional Chinese translations (§11 risk 3).
"""
from __future__ import annotations

from typing import List

from app.domain.library import Hymn, HymnLyricSection


def _h(idx: int, label: str, text: str) -> HymnLyricSection:
    return HymnLyricSection(order=idx, label=label, text=text)


def default_hymns() -> List[Hymn]:
    return [
        Hymn(
            id="default-doxology",
            title="三一颂",
            author="Thomas Ken",
            number="",
            source="公有领域",
            sections=[
                _h(
                    0,
                    "",
                    "赞美真神万福之源，\n天下生灵都当颂言，\n"
                    "天上万军颂赞主名，\n赞美圣父圣子圣灵。阿们。",
                )
            ],
        ),
        Hymn(
            id="default-amazing-grace",
            title="奇异恩典",
            author="John Newton",
            number="",
            source="公有领域",
            sections=[
                _h(0, "第一节", "奇异恩典，何等甘甜，我罪已得赦免；\n前我失丧，今被寻回，瞎眼今得看见。"),
                _h(1, "第二节", "如此恩典，使我敬畏，使我心得安慰；\n初信之时即蒙恩惠，真是何等宝贵。"),
                _h(2, "第三节", "许多危险，试炼网罗，我已安然经过；\n靠主恩典，安全不怕，更引导我归家。"),
                _h(3, "第四节", "将来在天，安居万年，光明灿烂如日；\n欢乐颂赞，永不减少，因主引领向前。"),
            ],
        ),
        Hymn(
            id="default-holy-holy-holy",
            title="圣哉三一",
            author="Reginald Heber",
            number="",
            source="公有领域",
            sections=[
                _h(0, "第一节", "圣哉，圣哉，圣哉！全能大主宰！\n清晨我众歌声穿云上达至尊前。"),
                _h(1, "第二节", "圣哉，圣哉，圣哉！慈悲与全能！\n荣耀与赞美，同归三一真神。"),
            ],
        ),
        Hymn(
            id="default-to-god-be-the-glory",
            title="荣耀归于真神",
            author="Fanny J. Crosby",
            number="",
            source="公有领域",
            sections=[
                _h(0, "第一节", "荣耀归于真神，他成就大事，\n为爱世人甚至赐下独生子。"),
                _h(1, "副歌", "赞美主！赞美主！全地当听主声音！\n赞美主！赞美主！万民都当来欢欣！"),
            ],
        ),
    ]
