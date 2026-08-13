"""Display-time verse text transforms."""

import unicodedata

from app.services.text_transform import (
    PunctuationTransform,
    ShenSpacingTransform,
    TransformPipeline,
    verse_display_pipeline,
)
from app.services.text_transform.punctuation import CONTEMPORARY_QUOTE_MAP


def test_quote_map_contains_only_single_punctuation_codepoints():
    for src, dst in CONTEMPORARY_QUOTE_MAP.items():
        assert len(src) == 1 and len(dst) == 1
        assert unicodedata.category(src).startswith("P")
        assert unicodedata.category(dst).startswith("P")


def test_punctuation_replaces_corner_quotes_only():
    raw = "神说：「要有光」，就有了光。"
    assert PunctuationTransform().apply(raw) == "神说：“要有光”，就有了光。"


def test_punctuation_maps_nested_quotes():
    raw = "说：「撒拉为什么暗笑，说：『我既已年老，果真能生养吗？』"
    out = PunctuationTransform().apply(raw)
    assert out == "说：“撒拉为什么暗笑，说：‘我既已年老，果真能生养吗？’"
    assert "「" not in out and "『" not in out


def test_punctuation_replaces_unpaired_quotes_per_character():
    assert PunctuationTransform().apply("「未闭合") == "“未闭合"
    assert PunctuationTransform().apply("未闭合」") == "未闭合”"


def test_punctuation_maps_vertical_presentation_forms():
    raw = "﹁外层﹃内层﹄外层﹂"
    assert PunctuationTransform().apply(raw) == "“外层‘内层’外层”"


def test_punctuation_does_not_change_wording_or_non_quote_marks():
    raw = "起初，　神创造天地。[名叫 亚当]、牲畜、昆虫。（注）——〔新郎〕"
    out = PunctuationTransform().apply(raw)
    assert out == raw


def test_non_mapped_characters_are_byte_identical():
    raw = "起初，　神创造天地。又[造]众星，称光为「昼」。"
    out = PunctuationTransform().apply(raw)
    mapped = set(CONTEMPORARY_QUOTE_MAP)
    assert len(out) == len(raw)
    for src, dst in zip(raw, out):
        if src in mapped:
            assert dst == CONTEMPORARY_QUOTE_MAP[src]
        else:
            assert dst == src


def test_empty_and_none_like_strings():
    pipeline = verse_display_pipeline()
    assert pipeline.apply("") == ""
    assert PunctuationTransform().apply("") == ""


def test_pipeline_runs_stages_in_order():
    class Suffix:
        name = "suffix"

        def __init__(self, token: str) -> None:
            self._token = token

        def apply(self, text: str) -> str:
            return text + self._token

    out = TransformPipeline([Suffix("A"), Suffix("B")]).apply("x")
    assert out == "xAB"


def test_shen_spacing_strips_ideographic_and_ascii_space():
    transform = ShenSpacingTransform()
    assert transform.apply("起初，　神创造天地。") == "起初，神创造天地。"
    assert transform.apply("耶和华 神") == "耶和华神"


def test_shen_spacing_leaves_other_god_contexts_unchanged():
    transform = ShenSpacingTransform()
    assert transform.apply("神说：「要有光」") == "神说：「要有光」"
    assert transform.apply("你们的神") == "你们的神"
    assert transform.apply("去随从别神") == "去随从别神"
    assert transform.apply("[名叫 亚当]") == "[名叫 亚当]"


def test_verse_display_pipeline_registers_punctuation_then_shen_spacing():
    pipeline = verse_display_pipeline()
    assert [stage.name for stage in pipeline.stages] == [
        "punctuation",
        "shen_spacing",
    ]
    assert pipeline.apply("说：『不可吃』") == "说：‘不可吃’"
    assert pipeline.apply("起初，　神说：「要有光」") == "起初，神说：“要有光”"
