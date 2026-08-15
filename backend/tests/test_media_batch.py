"""Batch media import service and API contracts."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.v1 import projects as projects_api
from app.domain.project import Project
from app.main import create_app
from app.services.project_store import ProjectStore


def _write(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_batch_import_partially_succeeds_and_persists_once(
    temp_data_dir, tmp_path, monkeypatch
):
    store = ProjectStore()
    project = store.create(name="批量媒体")
    image = _write(tmp_path / "valid.png", b"IMAGE")
    wrong_kind = _write(tmp_path / "wrong.wav", b"AUDIO")
    unsupported = _write(tmp_path / "notes.txt", b"TEXT")
    missing = tmp_path / "missing.png"

    write_count = 0
    original_write = store.write_file

    def count_write(saved_project: Project, path=None):
        nonlocal write_count
        write_count += 1
        return original_write(saved_project, path)

    monkeypatch.setattr(store, "write_file", count_write)
    result = store.import_media_batch(
        project.id,
        [str(image), str(wrong_kind), str(unsupported), str(missing)],
        kind="image",
    )

    assert write_count == 1
    assert [asset.name for asset in result.assets] == ["valid"]
    assert [failure.source_path for failure in result.failed] == [
        str(wrong_kind),
        str(unsupported),
        str(missing),
    ]
    assert [failure.code for failure in result.failed] == [
        "VALIDATION_ERROR",
        "VALIDATION_ERROR",
        "NOT_FOUND",
    ]
    persisted = Project.model_validate_json(
        (store.work_dir(project.id) / "project.json").read_text(encoding="utf-8")
    )
    assert [asset.ref for asset in persisted.media_assets] == [
        result.assets[0].ref
    ]


def test_batch_import_all_failures_do_not_persist(
    temp_data_dir, tmp_path, monkeypatch
):
    store = ProjectStore()
    project = store.create(name="失败批次")
    write_count = 0

    def count_write(*_args, **_kwargs):
        nonlocal write_count
        write_count += 1

    monkeypatch.setattr(store, "write_file", count_write)
    result = store.import_media_batch(
        project.id, [str(tmp_path / "missing.png")], kind="image"
    )

    assert result.assets == []
    assert len(result.failed) == 1
    assert result.failed[0].code == "NOT_FOUND"
    assert write_count == 0
    assert project.media_assets == []


def test_batch_import_keeps_both_same_named_files(temp_data_dir, tmp_path):
    store = ProjectStore()
    project = store.create(name="重名媒体")
    first = _write(tmp_path / "first" / "same.png", b"FIRST")
    second = _write(tmp_path / "second" / "same.png", b"SECOND")

    result = store.import_media_batch(
        project.id, [str(first), str(second)], kind="image"
    )

    assert len(result.assets) == 2
    assert result.failed == []
    assert [asset.kind for asset in result.assets] == ["image", "image"]
    assert len(project.media_assets) == 2
    assert result.assets[0].ref == "media/same.png"
    assert result.assets[1].ref != result.assets[0].ref
    media_root = store.work_dir(project.id) / "media"
    assert (media_root / Path(result.assets[0].ref).name).read_bytes() == b"FIRST"
    assert (media_root / Path(result.assets[1].ref).name).read_bytes() == b"SECOND"


def test_batch_import_api_contract_and_validation(
    temp_data_dir, tmp_path, monkeypatch
):
    store = ProjectStore()
    project = store.create(name="接口批次")
    image = _write(tmp_path / "api.png", b"IMAGE")
    monkeypatch.setattr(projects_api, "project_store", store)
    client = TestClient(create_app())

    response = client.post(
        f"/api/v1/projects/{project.id}/media/batch",
        json={
            "source_paths": [str(image), str(tmp_path / "missing.png")],
            "kind": "image",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["assets"]) == 1
    assert data["failed"] == [
        {
            "source_path": str(tmp_path / "missing.png"),
            "code": "NOT_FOUND",
            "message": f"媒体文件不存在: {tmp_path / 'missing.png'}",
        }
    ]

    empty = client.post(
        f"/api/v1/projects/{project.id}/media/batch",
        json={"source_paths": [], "kind": "image"},
    )
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "VALIDATION_ERROR"

    invalid_kind = client.post(
        f"/api/v1/projects/{project.id}/media/batch",
        json={"source_paths": [str(image)], "kind": "document"},
    )
    assert invalid_kind.status_code == 422
    assert invalid_kind.json()["error"]["code"] == "VALIDATION_ERROR"
