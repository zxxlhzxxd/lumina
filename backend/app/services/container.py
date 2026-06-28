"""Zip container pack/unpack for portable Lumina `.lumina` files.

A container is a zip holding:
    manifest.json   -> { kind, schema_version }
    <json_name>     -> project.json | template.json
    media/...       -> bundled media files (images / audio / video)
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.core.errors import AppError

MANIFEST_NAME = "manifest.json"
CONTAINER_SCHEMA_VERSION = 1

PROJECT_JSON = "project.json"
TEMPLATE_JSON = "template.json"


def pack(work_dir: Path, json_name: str, out_path: Path, kind: str) -> Path:
    """Pack a working directory (json + media/) into a zip container at out_path."""
    json_path = work_dir / json_name
    if not json_path.exists():
        raise AppError(f"找不到要打包的内容: {json_name}")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"kind": kind, "schema_version": CONTAINER_SCHEMA_VERSION}
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
