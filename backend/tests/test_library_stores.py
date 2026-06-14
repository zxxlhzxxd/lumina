"""Tests for hymn / liturgy library stores (seeding, CRUD, duplicate)."""
import pytest

from app.core.errors import AppError
from app.domain.library import Hymn, HymnLyricSection, LiturgyText
from app.services.hymn_store import HymnStore
from app.services.liturgy_store import LiturgyStore


def test_hymn_seed_and_search(temp_data_dir):
    store = HymnStore()
    builtins = store.search()
    assert len(builtins) >= 4
    assert all(h.builtin for h in builtins)
    # Search by title keyword.
    hits = store.search("奇异")
    assert any("奇异恩典" == h.title for h in hits)


def test_hymn_create_update_duplicate(temp_data_dir):
    store = HymnStore()
    created = store.create(
        Hymn(title="自建诗歌", sections=[HymnLyricSection(order=0, text="第一句")])
    )
    assert not created.builtin
    fetched = store.get(created.id)
    assert fetched.title == "自建诗歌"
    fetched.title = "改名"
    updated = store.update(created.id, fetched)
    assert updated.title == "改名"
    store.delete(created.id)


def test_hymn_builtin_is_readonly(temp_data_dir):
    store = HymnStore()
    builtin = store.search()[0]
    with pytest.raises(AppError):
        store.update(builtin.id, builtin)
    with pytest.raises(AppError):
        store.delete(builtin.id)
    copy = store.duplicate(builtin.id)
    assert not copy.builtin
    assert copy.title.endswith("副本")


def test_liturgy_seed_and_crud(temp_data_dir):
    store = LiturgyStore()
    builtins = store.list()
    assert any(t.title == "使徒信经" for t in builtins)
    created = store.create(LiturgyText(title="自定礼文", paragraphs=["一段"]))
    assert not created.builtin
    copy = store.duplicate(builtins[0].id)
    assert not copy.builtin
    with pytest.raises(AppError):
        store.delete(builtins[0].id)
    store.delete(created.id)
