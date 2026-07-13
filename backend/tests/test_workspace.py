"""Tests for workspace features: notes, bookmarks, collections, reading status."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.modules.bookmark.service.service import BookmarkService
from app.modules.collection.service.service import CollectionService
from app.modules.notes.service.service import NoteService
from app.modules.reading_status.service.service import ReadingStatusService

# ── Helper ────────────────────────────────────────────────────────


def _fake_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Notes ─────────────────────────────────────────────────────────


class TestNoteService:
    def test_create_note(self) -> None:
        repo = MagicMock()
        expected = MagicMock()
        expected.title = "Test"
        repo.create.return_value = expected
        service = NoteService(repo)
        inv_id = _fake_uuid()
        note = service.create_note(inv_id, title="Test", content="# Hello")
        repo.create.assert_called_once()
        assert note.title == "Test"

    def test_get_note_not_found(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = None
        service = NoteService(repo)
        with pytest.raises(HTTPException) as exc:
            service.get_note(_fake_uuid())
        assert exc.value.status_code == 404

    def test_get_note_found(self) -> None:
        repo = MagicMock()
        fake_note = MagicMock()
        fake_note.id = _fake_uuid()
        repo.get_by_id.return_value = fake_note
        service = NoteService(repo)
        result = service.get_note(_fake_uuid())
        assert result.id == fake_note.id

    def test_list_notes(self) -> None:
        repo = MagicMock()
        repo.list_by_investigation.return_value = [MagicMock(), MagicMock()]
        service = NoteService(repo)
        notes = service.list_notes(_fake_uuid())
        assert len(notes) == 2

    def test_list_notes_with_source_filter(self) -> None:
        repo = MagicMock()
        service = NoteService(repo)
        inv_id = _fake_uuid()
        service.list_notes(inv_id, source_type="copilot")
        repo.list_by_investigation.assert_called_with(inv_id, source_type="copilot")

    def test_search_notes(self) -> None:
        repo = MagicMock()
        repo.search.return_value = [MagicMock()]
        service = NoteService(repo)
        results = service.search_notes(_fake_uuid(), "transformer")
        assert len(results) == 1
        repo.search.assert_called_once()

    def test_search_notes_empty_query(self) -> None:
        repo = MagicMock()
        repo.list_by_investigation.return_value = [MagicMock()]
        service = NoteService(repo)
        results = service.search_notes(_fake_uuid(), "  ")
        assert len(results) == 1
        repo.list_by_investigation.assert_called_once()

    def test_update_note_partial(self) -> None:
        fake_id = _fake_uuid()
        repo = MagicMock()
        updated = MagicMock()
        updated.title = "Updated"
        repo.update.return_value = updated
        service = NoteService(repo)
        result = service.update_note(fake_id, content="New content")
        repo.update.assert_called_with(fake_id, content="New content")
        assert result.title == "Updated"

    def test_update_note_no_changes(self) -> None:
        fake_id = _fake_uuid()
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        service = NoteService(repo)
        result = service.update_note(fake_id)
        assert result is not None

    def test_delete_note_not_found(self) -> None:
        repo = MagicMock()
        repo.delete.return_value = False
        service = NoteService(repo)
        with pytest.raises(HTTPException) as exc:
            service.delete_note(_fake_uuid())
        assert exc.value.status_code == 404

    def test_delete_note_success(self) -> None:
        repo = MagicMock()
        repo.delete.return_value = True
        service = NoteService(repo)
        service.delete_note(_fake_uuid())
        repo.delete.assert_called_once()

    def test_add_link(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()  # note exists
        service = NoteService(repo)
        service.add_link(_fake_uuid(), "paper", "paper:123")
        repo.create_link.assert_called_once()

    def test_list_links(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        repo.list_links.return_value = [MagicMock()]
        service = NoteService(repo)
        links = service.list_links(_fake_uuid())
        assert len(links) == 1

    def test_delete_link_not_found(self) -> None:
        repo = MagicMock()
        repo.delete_link.return_value = False
        service = NoteService(repo)
        with pytest.raises(HTTPException) as exc:
            service.delete_link(_fake_uuid())
        assert exc.value.status_code == 404

    def test_create_highlight(self) -> None:
        repo = MagicMock()
        service = NoteService(repo)
        service.create_note(
            _fake_uuid(),
            title="Highlight",
            content="Selected text",
            source_type="copilot",
            source_id="msg:42",
            source_context="original highlighted text",
        )
        repo.create.assert_called_once()
        args = repo.create.call_args[0][0]
        assert args.source_type == "copilot"
        assert args.source_id == "msg:42"
        assert args.source_context == "original highlighted text"

    def test_note_autosave_supports_partial_update(self) -> None:
        repo = MagicMock()
        updated = MagicMock()
        updated.content = "Autosaved content"
        repo.update.return_value = updated
        service = NoteService(repo)
        result = service.update_note(_fake_uuid(), content="Autosaved content")
        assert result.content == "Autosaved content"


# ── Bookmarks ─────────────────────────────────────────────────────


class TestBookmarkService:
    def test_add_bookmark(self) -> None:
        repo = MagicMock()
        repo.get_by_paper.return_value = None
        service = BookmarkService(repo)
        inv_id = _fake_uuid()
        paper_id = _fake_uuid()
        bookmark = service.add_bookmark(inv_id, paper_id)
        repo.create.assert_called_once()
        assert bookmark is not None

    def test_add_duplicate_bookmark_returns_existing(self) -> None:
        repo = MagicMock()
        existing = MagicMock()
        repo.get_by_paper.return_value = existing
        service = BookmarkService(repo)
        result = service.add_bookmark(_fake_uuid(), _fake_uuid())
        assert result == existing
        repo.create.assert_not_called()

    def test_list_bookmarks(self) -> None:
        repo = MagicMock()
        repo.list_by_investigation.return_value = [MagicMock(), MagicMock()]
        service = BookmarkService(repo)
        bookmarks = service.list_bookmarks(_fake_uuid())
        assert len(bookmarks) == 2

    def test_remove_bookmark(self) -> None:
        repo = MagicMock()
        repo.delete.return_value = True
        service = BookmarkService(repo)
        service.remove_bookmark(_fake_uuid())
        repo.delete.assert_called_once()

    def test_remove_bookmark_not_found(self) -> None:
        repo = MagicMock()
        repo.delete.return_value = False
        service = BookmarkService(repo)
        with pytest.raises(HTTPException) as exc:
            service.remove_bookmark(_fake_uuid())
        assert exc.value.status_code == 404


# ── Collections ───────────────────────────────────────────────────


class TestCollectionService:
    def test_create_collection(self) -> None:
        repo = MagicMock()
        expected = MagicMock()
        expected.name = "Baseline Papers"
        repo.create.return_value = expected
        service = CollectionService(repo)
        inv_id = _fake_uuid()
        collection = service.create_collection(inv_id, "Baseline Papers")
        repo.create.assert_called_once()
        assert collection.name == "Baseline Papers"

    def test_get_collection_not_found(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = None
        service = CollectionService(repo)
        with pytest.raises(HTTPException) as exc:
            service.get_collection(_fake_uuid())
        assert exc.value.status_code == 404

    def test_list_collections(self) -> None:
        repo = MagicMock()
        repo.list_by_investigation.return_value = [MagicMock(), MagicMock()]
        service = CollectionService(repo)
        collections = service.list_collections(_fake_uuid())
        assert len(collections) == 2

    def test_update_collection(self) -> None:
        fake_id = _fake_uuid()
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        updated = MagicMock()
        updated.name = "New Name"
        repo.update.return_value = updated
        service = CollectionService(repo)
        result = service.update_collection(fake_id, name="New Name")
        assert result.name == "New Name"

    def test_delete_collection(self) -> None:
        repo = MagicMock()
        repo.delete.return_value = True
        service = CollectionService(repo)
        service.delete_collection(_fake_uuid())
        repo.delete.assert_called_once()

    def test_add_paper_to_collection(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        service = CollectionService(repo)
        service.add_paper(_fake_uuid(), _fake_uuid())
        repo.add_paper.assert_called_once()

    def test_remove_paper_from_collection(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        repo.remove_paper.return_value = True
        service = CollectionService(repo)
        service.remove_paper(_fake_uuid(), _fake_uuid())
        repo.remove_paper.assert_called_once()

    def test_remove_paper_not_found(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        repo.remove_paper.return_value = False
        service = CollectionService(repo)
        with pytest.raises(HTTPException) as exc:
            service.remove_paper(_fake_uuid(), _fake_uuid())
        assert exc.value.status_code == 404

    def test_paper_belongs_to_multiple_collections(self) -> None:
        repo = MagicMock()
        repo.get_by_id.return_value = MagicMock()
        service = CollectionService(repo)
        paper_id = _fake_uuid()
        # Add same paper to two different collections
        service.add_paper(_fake_uuid(), paper_id)
        service.add_paper(_fake_uuid(), paper_id)
        assert repo.add_paper.call_count == 2


# ── Reading Status ────────────────────────────────────────────────


class TestReadingStatusService:
    def test_set_status(self) -> None:
        repo = MagicMock()
        result = MagicMock()
        result.status = "reading"
        repo.upsert.return_value = result
        service = ReadingStatusService(repo)
        status = service.set_status(_fake_uuid(), _fake_uuid(), "reading")
        assert status.status == "reading"
        repo.upsert.assert_called_once()

    def test_set_invalid_status_defaults_to_unread(self) -> None:
        repo = MagicMock()
        result = MagicMock()
        result.status = "unread"
        repo.upsert.return_value = result
        service = ReadingStatusService(repo)
        status = service.set_status(_fake_uuid(), _fake_uuid(), "invalid")
        assert status.status == "unread"

    def test_get_status(self) -> None:
        repo = MagicMock()
        expected = MagicMock()
        repo.get.return_value = expected
        service = ReadingStatusService(repo)
        result = service.get_status(_fake_uuid(), _fake_uuid())
        assert result == expected

    def test_get_status_none(self) -> None:
        repo = MagicMock()
        repo.get.return_value = None
        service = ReadingStatusService(repo)
        result = service.get_status(_fake_uuid(), _fake_uuid())
        assert result is None

    def test_list_by_investigation(self) -> None:
        repo = MagicMock()
        repo.list_by_investigation.return_value = [MagicMock(), MagicMock()]
        service = ReadingStatusService(repo)
        results = service.list_by_investigation(_fake_uuid())
        assert len(results) == 2
