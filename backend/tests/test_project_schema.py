import json

from app.domain.project import Project
from app.domain.media import MediaAsset
from app.domain.sections import CoverSection, LiturgyTextSection, MediaSection
from app.domain.style import (
    BlockLayout,
    EdgeInsets,
    SectionStyle,
    TextBlockStyle,
    TextStyle,
)
from app.services.project_store import ProjectStore


def test_legacy_theme_id_is_ignored_on_save_shape():
    project = Project.model_validate(
        {
            "id": "legacy",
            "name": "旧工程",
            "slide_size": "16:9",
            "theme_id": "builtin-dawn",
            "sections": [],
            "meta": {},
        }
    )
    data = json.loads(project.model_dump_json())
    assert "theme_id" not in data


def test_legacy_media_caption_migrates_to_body():
    project = Project.model_validate(
        {
            "sections": [
                {
                    "type": "media",
                    "title": "起立默祷",
                    "caption": "请起立默祷",
                }
            ]
        }
    )

    section = project.sections[0]
    assert isinstance(section, MediaSection)
    assert section.body == "请起立默祷"

    data = json.loads(project.model_dump_json())
    assert data["sections"][0]["body"] == "请起立默祷"
    assert "caption" not in data["sections"][0]


def test_legacy_media_title_migrates_to_slide_title():
    project = Project.model_validate(
        {
            "sections": [
                {
                    "type": "media",
                    "title": "起立默祷",
                    "body": "请起立默祷",
                }
            ]
        }
    )

    section = project.sections[0]
    assert isinstance(section, MediaSection)
    assert section.title == "起立默祷"
    assert section.slide_title == "起立默祷"

    data = json.loads(project.model_dump_json())
    assert data["sections"][0]["slide_title"] == "起立默祷"


def test_legacy_media_refs_migrate_to_media_assets():
    project = Project.model_validate(
        {
            "sections": [
                {
                    "type": "cover",
                    "style": {"background_image": "media/bg.png"},
                },
                {
                    "type": "media",
                    "audio_ref": "media/prayer.wav",
                    "video_ref": "media/placeholder.mp4",
                },
            ]
        }
    )

    assets = {asset.ref: asset.kind for asset in project.media_assets}
    assert assets == {
        "media/bg.png": "image",
        "media/prayer.wav": "audio",
        "media/placeholder.mp4": "video",
    }


def test_media_assets_roundtrip_in_project():
    project = Project(
        media_assets=[
            MediaAsset(
                id="asset-1",
                kind="audio",
                name="默祷音频",
                ref="media/prayer.wav",
            )
        ]
    )
    restored = Project.model_validate_json(project.model_dump_json())
    assert restored.media_assets[0].id == "asset-1"
    assert restored.media_assets[0].name == "默祷音频"


def test_legacy_liturgy_title_migrates_to_slide_title():
    project = Project.model_validate(
        {
            "sections": [
                {
                    "type": "liturgy_text",
                    "title": "使徒信经",
                    "paragraphs": ["我信上帝"],
                }
            ]
        }
    )

    section = project.sections[0]
    assert isinstance(section, LiturgyTextSection)
    assert section.title == "使徒信经"
    assert section.slide_title == "使徒信经"


def test_extended_font_style_fields_serialize_in_project():
    project = Project(
        sections=[
            CoverSection(
                style=SectionStyle(
                    title=TextStyle(
                        italic=True,
                        underline=True,
                        highlight_color="#FFF200",
                    )
                )
            )
        ]
    )
    restored = Project.model_validate_json(project.model_dump_json())
    title_style = restored.sections[0].style.title
    assert title_style.italic is True
    assert title_style.underline is True
    assert title_style.highlight_color == "#FFF200"


def test_project_duplicate_preserves_extended_font_style(temp_data_dir):
    store = ProjectStore()
    project = store.create(name="字体工程")
    project.sections = [
        CoverSection(
            style=SectionStyle(
                title=TextStyle(
                    italic=True,
                    underline=True,
                    highlight_color="#FFF200",
                )
            )
        )
    ]

    copied = store.duplicate(project.id)
    copied_style = copied.sections[0].style.title
    assert copied_style.italic is True
    assert copied_style.underline is True
    assert copied_style.highlight_color == "#FFF200"


def test_project_roundtrip_preserves_text_block_layout():
    project = Project(
        sections=[
            CoverSection(
                style=SectionStyle(
                    blocks={
                        "title": TextBlockStyle(
                            text=TextStyle(
                                color="#123456",
                                vertical_align="bottom",
                            ),
                            layout=BlockLayout(
                                anchor="bottom_right",
                                margin=EdgeInsets(
                                    top=0.2,
                                    right=0.3,
                                    bottom=0.4,
                                    left=0.5,
                                ),
                            ),
                        )
                    }
                )
            )
        ]
    )
    restored = Project.model_validate_json(project.model_dump_json())
    block = restored.sections[0].style.blocks["title"]
    assert block.text.color == "#123456"
    assert block.text.vertical_align == "bottom"
    assert block.layout.anchor == "bottom_right"
    assert block.layout.margin.model_dump() == {
        "top": 0.2,
        "right": 0.3,
        "bottom": 0.4,
        "left": 0.5,
    }


def test_legacy_layout_blocks_migrate_to_unified_block_styles():
    project = Project.model_validate(
        {
            "sections": [
                {
                    "type": "cover",
                    "style": {
                        "layout": {
                            "blocks": {
                                "title": {
                                    "anchor": "top_left",
                                    "margin": {"top": 0.3, "left": 0.4},
                                }
                            }
                        }
                    },
                }
            ]
        }
    )
    style = project.sections[0].style
    assert style.blocks["title"].layout.anchor == "top_left"
    data = json.loads(project.model_dump_json())
    assert "layout" not in data["sections"][0]["style"]
