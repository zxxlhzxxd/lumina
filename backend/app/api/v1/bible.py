"""Bible endpoints: books, reference parsing, passage lookup."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.responses import ok
from app.services.bible_service import bible_service

router = APIRouter(prefix="/bible", tags=["bible"])


class ParseRefBody(BaseModel):
    ref: str


@router.get("/books")
def get_books() -> dict:
    return ok([b.model_dump() for b in bible_service.get_books()])


@router.get("/books/{book_id}/chapters")
def get_chapters(book_id: int) -> dict:
    return ok(bible_service.get_chapters(book_id))


@router.get("/passage")
def get_passage(ref: str) -> dict:
    reference, verses = bible_service.get_passage(ref)
    return ok(
        {
            "reference": reference.model_dump(),
            "verses": [v.model_dump() for v in verses],
        }
    )


@router.post("/parse-ref")
def parse_ref(body: ParseRefBody) -> dict:
    reference = bible_service.parse_reference(body.ref)
    return ok({"reference": reference.model_dump()})
