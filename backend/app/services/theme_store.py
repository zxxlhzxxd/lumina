"""Visual-theme store: built-in (read-only) + user themes (JSON files).

User themes persist as `themes/<id>.json` in the data dir. The default theme id
is recorded in `preferences.json`. Built-in themes can be duplicated into
editable user copies.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.errors import AppError, NotFoundError
from app.data.theme_seed import builtin_themes, default_theme_id
from app.domain.project import Theme

logger = logging.getLogger(__name__)


def _new_id() -> str:
    return uuid4().hex


class ThemeStore:
    def __init__(self) -> None:
        self._builtins: Dict[str, Theme] = {t.id: t for t in builtin_themes()}

    # ---- helpers ---------------------------------------------------------
    def _path(self, theme_id: str) -> Path:
        settings.ensure_dirs()
        return settings.themes_dir / f"{theme_id}.json"

    def _load_users(self) -> Dict[str, Theme]:
        settings.ensure_dirs()
        users: Dict[str, Theme] = {}
        for path in settings.themes_dir.glob("*.json"):
            try:
                theme = Theme.model_validate_json(path.read_text(encoding="utf-8"))
                theme.builtin = False
                users[theme.id] = theme
            except Exception as exc:  # noqa: BLE001
                logger.warning("跳过损坏的主题文件 %s: %s", path.name, exc)
        return users

    def _read_prefs(self) -> dict:
        if settings.prefs_path.exists():
            try:
                return json.loads(settings.prefs_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _write_prefs(self, prefs: dict) -> None:
        settings.ensure_dirs()
        settings.prefs_path.write_text(
            json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- read ------------------------------------------------------------
    def list(self) -> List[Theme]:
        items = list(self._builtins.values()) + list(self._load_users().values())
        return items

    def get(self, theme_id: Optional[str]) -> Optional[Theme]:
        if not theme_id:
            return None
        if theme_id in self._builtins:
            return self._builtins[theme_id].model_copy(deep=True)
        path = self._path(theme_id)
        if path.exists():
            theme = Theme.model_validate_json(path.read_text(encoding="utf-8"))
            theme.builtin = False
            return theme
        return None

    def get_or_default(self, theme_id: Optional[str]) -> Theme:
        theme = self.get(theme_id)
        if theme is not None:
            return theme
        theme = self.get(self.default_id)
        if theme is not None:
            return theme
        return next(iter(self._builtins.values())).model_copy(deep=True)

    @property
    def default_id(self) -> str:
        prefs = self._read_prefs()
        candidate = prefs.get("default_theme_id")
        if candidate and self.get(candidate) is not None:
            return candidate
        return default_theme_id()

    # ---- write -----------------------------------------------------------
    def _save_user(self, theme: Theme) -> Theme:
        theme.builtin = False
        self._path(theme.id).write_text(
            theme.model_dump_json(indent=2), encoding="utf-8"
        )
        return theme

    def create(self, theme: Theme) -> Theme:
        theme = theme.model_copy(deep=True)
        theme.id = _new_id()
        return self._save_user(theme)

    def update(self, theme_id: str, theme: Theme) -> Theme:
        if theme_id in self._builtins:
            raise AppError("内置主题为只读，请先复制后再编辑")
        if not self._path(theme_id).exists():
            raise NotFoundError(f"主题不存在: {theme_id}")
        theme = theme.model_copy(deep=True)
        theme.id = theme_id
        return self._save_user(theme)

    def delete(self, theme_id: str) -> None:
        if theme_id in self._builtins:
            raise AppError("内置主题不可删除")
        path = self._path(theme_id)
        if not path.exists():
            raise NotFoundError(f"主题不存在: {theme_id}")
        path.unlink()
        prefs = self._read_prefs()
        if prefs.get("default_theme_id") == theme_id:
            prefs.pop("default_theme_id", None)
            self._write_prefs(prefs)

    def duplicate(self, theme_id: str) -> Theme:
        source = self.get(theme_id)
        if source is None:
            raise NotFoundError(f"主题不存在: {theme_id}")
        copy = source.model_copy(deep=True)
        copy.id = _new_id()
        copy.builtin = False
        copy.name = f"{source.name} 副本"
        return self._save_user(copy)

    def set_default(self, theme_id: str) -> str:
        if self.get(theme_id) is None:
            raise NotFoundError(f"主题不存在: {theme_id}")
        prefs = self._read_prefs()
        prefs["default_theme_id"] = theme_id
        self._write_prefs(prefs)
        return theme_id


theme_store = ThemeStore()
