import json

from app.domain.project import Project


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
