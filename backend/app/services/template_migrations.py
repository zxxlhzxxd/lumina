"""Version policy and migration registry for portable service templates."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services import container

TEMPLATE_SCHEMA_VERSION = 1

# Register future migrations by their source version. Each migration receives
# the entire extracted work directory and advances exactly one version.
TEMPLATE_MIGRATIONS: dict[int, container.Migration] = {}


def unpack_and_migrate(
    container_path: Path, dest_work_dir: Path
) -> dict[str, Any]:
    return container.unpack_versioned(
        container_path,
        dest_work_dir,
        expected_kind="template",
        current_version=TEMPLATE_SCHEMA_VERSION,
        migrations=TEMPLATE_MIGRATIONS,
    )
