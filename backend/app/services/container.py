"""Zip container pack/unpack for portable Lumina `.lumina` files.

A container is a zip holding:
    manifest.json   -> { kind, schema_version }
    <json_name>     -> project.json | template.json
    media/...       -> bundled media files (images / audio / video)
"""
from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from app.core.errors import AppError

MANIFEST_NAME = "manifest.json"
CONTAINER_SCHEMA_VERSION = 1

PROJECT_JSON = "project.json"
TEMPLATE_JSON = "template.json"


@dataclass(frozen=True)
class MigrationContext:
    """Mutable container contents available to one schema migration step."""

    work_dir: Path
    manifest: dict[str, Any]


Migration = Callable[[MigrationContext], None]


def pack(
    work_dir: Path,
    json_name: str,
    out_path: Path,
    kind: str,
    *,
    schema_version: int = CONTAINER_SCHEMA_VERSION,
) -> Path:
    """Pack a working directory (json + media/) into a zip container at out_path."""
    json_path = work_dir / json_name
    if not json_path.exists():
        raise AppError(f"找不到要打包的内容: {json_name}")
    if type(schema_version) is not int or schema_version < 1:
        raise AppError("容器格式版本必须是大于等于 1 的整数")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"kind": kind, "schema_version": schema_version}
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.write(json_path, json_name)
        media = work_dir / "media"
        if media.is_dir():
            for f in sorted(media.rglob("*")):
                if f.is_file():
                    zf.write(f, str(f.relative_to(work_dir)))
    return out_path


def unpack(container_path: Path, dest_work_dir: Path) -> dict:
    """Extract a container into dest_work_dir.

    Returns the parsed manifest. Guards against path traversal (zip slip).
    """
    container_path = Path(container_path)
    if not container_path.exists():
        raise AppError(f"容器文件不存在: {container_path}")
    dest_work_dir.mkdir(parents=True, exist_ok=True)
    dest_root = dest_work_dir.resolve()
    try:
        with zipfile.ZipFile(container_path, "r") as zf:
            for member in zf.namelist():
                target = (dest_work_dir / member).resolve()
                if dest_root != target and dest_root not in target.parents:
                    raise AppError("容器包含非法路径，已拒绝解包")
            zf.extractall(dest_work_dir)
            manifest_member = zf.read(MANIFEST_NAME) if MANIFEST_NAME in zf.namelist() else None
    except zipfile.BadZipFile as exc:
        raise AppError("无效的容器文件（非 zip 格式）") from exc

    if manifest_member is not None:
        try:
            return json.loads(manifest_member.decode("utf-8"))
        except json.JSONDecodeError:
            pass
    return {"kind": "unknown", "schema_version": CONTAINER_SCHEMA_VERSION}


def unpack_versioned(
    container_path: Path,
    dest_work_dir: Path,
    *,
    expected_kind: str,
    current_version: int,
    migrations: Mapping[int, Migration],
) -> dict[str, Any]:
    """Strictly unpack and migrate a versioned container.

    Migrations are registered by their source version and always advance one
    version. The complete migration chain is checked before extraction, and a
    failed import never leaves the destination directory behind.
    """
    if type(current_version) is not int or current_version < 1:
        raise ValueError("current_version must be a positive integer")

    container_path = Path(container_path)
    dest_work_dir = Path(dest_work_dir)
    if not container_path.exists():
        raise AppError(f"容器文件不存在: {container_path}")
    if dest_work_dir.exists():
        raise AppError(f"导入目录已存在: {dest_work_dir}")

    try:
        with zipfile.ZipFile(container_path, "r") as zf:
            _validate_members(zf, dest_work_dir)
            manifest = _read_manifest(zf)
            source_version = _validate_manifest(
                manifest,
                expected_kind=expected_kind,
                current_version=current_version,
            )
            migration_steps = _migration_steps(
                source_version,
                current_version,
                migrations,
            )
            dest_work_dir.mkdir(parents=True)
            zf.extractall(dest_work_dir)
    except zipfile.BadZipFile as exc:
        if dest_work_dir.exists():
            shutil.rmtree(dest_work_dir, ignore_errors=True)
        raise AppError("无效的容器文件（非 zip 格式）") from exc
    except Exception:
        if dest_work_dir.exists():
            shutil.rmtree(dest_work_dir, ignore_errors=True)
        raise

    context = MigrationContext(work_dir=dest_work_dir, manifest=manifest)
    try:
        for source, migration in migration_steps:
            try:
                migration(context)
            except Exception as exc:
                raise AppError(
                    f"容器从版本 {source} 迁移到版本 {source + 1} 失败",
                    details={"source_version": source, "target_version": source + 1},
                ) from exc
            context.manifest["kind"] = expected_kind
            context.manifest["schema_version"] = source + 1
            _write_manifest(context)
        return context.manifest
    except Exception:
        shutil.rmtree(dest_work_dir, ignore_errors=True)
        raise


def _validate_members(zf: zipfile.ZipFile, dest_work_dir: Path) -> None:
    dest_root = dest_work_dir.resolve()
    for member in zf.namelist():
        target = (dest_work_dir / member).resolve()
        if dest_root != target and dest_root not in target.parents:
            raise AppError("容器包含非法路径，已拒绝解包")


def _read_manifest(zf: zipfile.ZipFile) -> dict[str, Any]:
    manifest_entries = [name for name in zf.namelist() if name == MANIFEST_NAME]
    if not manifest_entries:
        raise AppError("无效的容器：缺少 manifest.json")
    if len(manifest_entries) != 1:
        raise AppError("无效的容器：manifest.json 重复")
    try:
        payload = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AppError("无效的容器：manifest.json 格式错误") from exc
    if not isinstance(payload, dict):
        raise AppError("无效的容器：manifest.json 必须是 JSON 对象")
    return payload


def _validate_manifest(
    manifest: dict[str, Any],
    *,
    expected_kind: str,
    current_version: int,
) -> int:
    if manifest.get("kind") != expected_kind:
        raise AppError("无效的容器：类型不匹配")
    version = manifest.get("schema_version")
    if type(version) is not int or version < 1:
        raise AppError("无效的容器：schema_version 必须是大于等于 1 的整数")
    if version > current_version:
        raise AppError(
            f"不支持的容器文件版本 {version}（当前支持版本 {current_version}）",
            details={"file_version": version, "supported_version": current_version},
        )
    return version


def _migration_steps(
    source_version: int,
    current_version: int,
    migrations: Mapping[int, Migration],
) -> list[tuple[int, Migration]]:
    missing = [
        version
        for version in range(source_version, current_version)
        if version not in migrations
    ]
    if missing:
        raise AppError(
            f"无法将容器从版本 {source_version} 迁移到版本 {current_version}："
            f"缺少版本 {missing[0]} 到版本 {missing[0] + 1} 的迁移",
            details={
                "file_version": source_version,
                "supported_version": current_version,
                "missing_source_version": missing[0],
            },
        )
    return [
        (version, migrations[version])
        for version in range(source_version, current_version)
    ]


def _write_manifest(context: MigrationContext) -> None:
    (context.work_dir / MANIFEST_NAME).write_text(
        json.dumps(context.manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
