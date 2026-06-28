"""Tests for section -> slide expansion using a stub passage resolver."""
from app.domain.bible import BibleReference, RangeRef, Verse, VerseRef
from app.domain.project import Project
from app.domain.sections import (
    AnnouncementSection,
    CoverSection,
    HymnSection,
    LiturgyTextSection,
    MediaSection,
    ResponsiveReadingSection,
    ScriptureSection,
)
from app.domain.style import BlockLayout, SectionStyle, TextBlockStyle, TextStyle
from app.services.generation import build_section_slides, build_slides


def stub_resolver(_raw: str):
    ref = BibleReference(
        book_id=26,
        book_name="以西结书",
        ranges=[RangeRef(start=VerseRef(chapter=4, verse=1), end=VerseRef(chapter=4, verse=3))],
        display="以西结书 4:1-3",
    )
    verses = [
        Verse(book_id=26, book_name="以西结书", chapter=4, verse=i, text=f"第{i}节经文内容")
        for i in (1, 2, 3)
    ]
    return ref, verses


def test_responsive_alternates_roles():
    s = ResponsiveReadingSection(reference="以西结书4:1-3")
    slides = build_section_slides(s, stub_resolver)
    assert [sl.label for sl in slides] == ["启", "应", "合"]
    assert all(sl.kind == "responsive_verse" for sl in slides)


def test_responsive_start_with_ying():
    s = ResponsiveReadingSection(reference="以西结书4:1-3", start_role="ying")
    slides = build_section_slides(s, stub_resolver)
    assert [sl.label for sl in slides] == ["应", "启", "合"]


def test_scripture_title_and_pagination():
    s = ScriptureSection(reference="以西结书4:1-3", chars_per_slide=20)
    slides = build_section_slides(s, stub_resolver)
    assert slides[0].kind == "scripture_title"
    assert any(sl.kind == "scripture" for sl in slides)


def test_cover_single_slide():
    s = CoverSection(main_title="主日崇拜", sub_title="2026")
    slides = build_section_slides(s)
    assert len(slides) == 1 and slides[0].title == "主日崇拜"


def test_liturgy_uses_blank_line_as_page_break():
    s = LiturgyTextSection(
        title="礼文段落",
        slide_title="使徒信经",
        paragraphs=["A\nB\n\nC\nD"],
    )
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB", "C\nD"]
    assert [sl.title for sl in slides] == ["使徒信经", None]


def test_liturgy_keeps_extra_blank_lines_after_page_break():
    s = LiturgyTextSection(
        slide_title="礼文",
        paragraphs=["A\n\n\nB"],
    )
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A", "\nB"]


def test_liturgy_trailing_page_break_does_not_add_blank_slide():
    s = LiturgyTextSection(
        slide_title="礼文",
        paragraphs=["A\nB\n"],
    )
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB"]


def test_liturgy_empty_section_keeps_single_blank_slide():
    s = LiturgyTextSection(slide_title="礼文", paragraphs=[])
    slides = build_section_slides(s)
    assert len(slides) == 1
    assert slides[0].title == "礼文"
    assert slides[0].body == ""


def test_hymn_uses_blank_line_as_page_break():
    s = HymnSection(
        lyrics=["A\nB\n\nC\nD"],
        lines_per_slide=99,
        include_title_slide=False,
    )
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB", "C\nD"]


def test_hymn_keeps_extra_blank_lines_after_page_break():
    s = HymnSection(
        lyrics=["A\n\n\nB"],
        include_title_slide=False,
    )
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A", "\nB"]


def test_hymn_trailing_page_break_does_not_add_blank_slide():
    s = HymnSection(
        lyrics=["A\nB\n"],
        include_title_slide=False,
    )
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB"]


def test_announcement_does_not_add_bullets():
    s = AnnouncementSection(heading="家事报告", items=["A\nB"])
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB"]
    assert "•" not in slides[0].body


def test_announcement_uses_blank_line_as_page_break():
    s = AnnouncementSection(heading="家事报告", items=["A\nB\n\nC\nD"])
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB", "C\nD"]
    assert [sl.title for sl in slides] == ["家事报告", None]


def test_announcement_keeps_old_multi_item_format_as_lines():
    s = AnnouncementSection(heading="家事报告", items=["A", "B"])
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB"]


def test_announcement_trailing_page_break_does_not_add_blank_slide():
    s = AnnouncementSection(heading="家事报告", items=["A\nB\n"])
    slides = build_section_slides(s)
    assert [sl.body for sl in slides] == ["A\nB"]


def test_media_slide_carries_audio_playback_fields():
    s = MediaSection(
        title="媒体段落",
        slide_title="起立默祷",
        body="请起立默祷\n静候音乐结束",
        audio_ref="media/prayer.wav",
        play_mode="loop",
        audio_trigger="auto",
    )
    slides = build_section_slides(s)
    assert len(slides) == 1
    assert slides[0].kind == "media"
    assert slides[0].title == "起立默祷"
    assert slides[0].body == "请起立默祷\n静候音乐结束"
    assert slides[0].audio_ref == "media/prayer.wav"
    assert slides[0].play_mode == "loop"
    assert slides[0].audio_trigger == "auto"


def test_build_slides_injects_resolved_style():
    project = Project(sections=[CoverSection(main_title="标题")])
    slides = build_slides(project)
    assert slides[0].style is not None
    assert slides[0].style["background_color"] == "#F7F3E9"
    assert slides[0].style["body"]["font_size"] == 32


def test_build_slides_omits_empty_block_style_fields():
    project = Project(
        sections=[
            CoverSection(
                main_title="标题",
                style=SectionStyle(
                    blocks={
                        "title": TextBlockStyle(
                            text=TextStyle(vertical_align="bottom"),
                            layout=BlockLayout(anchor="bottom_center"),
                        )
                    }
                ),
            )
        ]
    )
    style = build_slides(project)[0].style
    assert style["title"]["font_family"] == "Microsoft YaHei"
    assert style["title"]["font_size"] == 54
    assert style["blocks"]["title"]["text"] == {"vertical_align": "bottom"}
    assert style["blocks"]["title"]["layout"] == {"anchor": "bottom_center"}
