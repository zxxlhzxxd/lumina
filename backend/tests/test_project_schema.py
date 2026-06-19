import json

from app.domain.project import Project
from app.domain.sections import CoverSection, MediaSection
from app.domain.style import SectionStyle, TextStyle
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
