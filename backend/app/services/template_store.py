"""Built-in service (worship-flow) templates.

Phase 1 ships one read-only default template matching the standard order of
worship (REQUIREMENTS §12). User-defined templates / persistence is phase 2.
"""
from __future__ import annotations

from typing import List, Optional

from app.domain.enums import PlayMode, SlideSize
from app.domain.project import ServiceTemplate
from app.domain.sections import (
    AnnouncementSection,
    CoverSection,
    HymnSection,
    LiturgyTextSection,
    MediaSection,
    ResponsiveReadingSection,
    ScriptureSection,
)

APOSTLES_CREED = [
    "我信上帝，全能的父，创造天地的主。",
    "我信我主耶稣基督，上帝独生的子；因圣灵感孕，由童贞女马利亚所生；"
    "在本丢彼拉多手下受难，被钉于十字架，受死，埋葬；降在阴间；"
    "第三天从死里复活；后升天，坐在全能父上帝的右边；"
    "将来必从那里降临，审判活人死人。",
    "我信圣灵；我信圣而公之教会；我信圣徒相通；我信罪得赦免；"
    "我信身体复活；我信永生。阿们。",
]

LORDS_PRAYER = [
    "我们在天上的父：愿人都尊你的名为圣。愿你的国降临；"
    "愿你的旨意行在地上，如同行在天上。",
    "我们日用的饮食，今日赐给我们。免我们的债，如同我们免了人的债。"
    "不叫我们遇见试探；救我们脱离凶恶。",
    "因为国度、权柄、荣耀，全是你的，直到永远。阿们。",
]

GLORIA = [
    "愿荣耀归于父、子、圣灵；起初这样，现在这样，以后也这样，永无穷尽。阿们。",
]


def _default_sunday_template() -> ServiceTemplate:
    sections = [
        CoverSection(title="礼拜封面", main_title="主日崇拜", sub_title=""),
        MediaSection(title="起立默祷", caption="请起立默祷", play_mode=PlayMode.ONCE),
        ResponsiveReadingSection(title="启应经文", reference=""),
        LiturgyTextSection(title="使徒信经", paragraphs=list(APOSTLES_CREED)),
        HymnSection(title="赞美诗（一）", song_title=""),
        HymnSection(title="赞美诗（二）", song_title=""),
        HymnSection(title="赞美诗（三）", song_title=""),
        LiturgyTextSection(title="祷告", paragraphs=[]),
        LiturgyTextSection(title="荣耀颂", paragraphs=list(GLORIA)),
        ScriptureSection(title="证道经文", reference=""),
        CoverSection(title="证道题目", main_title=""),
        LiturgyTextSection(title="回应祷告", paragraphs=[]),
        HymnSection(title="回应诗歌", song_title=""),
        AnnouncementSection(title="家事报告", heading="家事报告", items=[]),
        HymnSection(title="结束诗歌", song_title=""),
        LiturgyTextSection(title="主祷文", paragraphs=list(LORDS_PRAYER)),
        MediaSection(title="阿门颂", caption="", play_mode=PlayMode.ONCE),
    ]
    return ServiceTemplate(
        id="builtin-sunday",
        name="主日崇拜（默认）",
        builtin=True,
        description="标准主日崇拜流程模板",
        slide_size=SlideSize.WIDE,
        sections=sections,
    )


class TemplateStore:
    def __init__(self) -> None:
        self._builtins = {t.id: t for t in [_default_sunday_template()]}

    def list_templates(self) -> List[ServiceTemplate]:
        # Rebuild to ensure fresh ids on the section instances each call.
        return [self.get(t_id) for t_id in self._builtins]

    def get(self, template_id: str) -> Optional[ServiceTemplate]:
        if template_id == "builtin-sunday":
            return _default_sunday_template()
        return None

    @property
    def default_id(self) -> str:
        return "builtin-sunday"


template_store = TemplateStore()
