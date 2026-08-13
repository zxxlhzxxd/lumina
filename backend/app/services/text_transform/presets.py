"""Policy: which transform stages run for each presentation surface."""

from __future__ import annotations

from app.services.text_transform.base import TransformPipeline
from app.services.text_transform.punctuation import PunctuationTransform
from app.services.text_transform.shen_spacing import ShenSpacingTransform


def verse_display_pipeline() -> TransformPipeline:
    """Default pipeline for Bible verse presentation."""
    return TransformPipeline(
        [
            PunctuationTransform(),
            ShenSpacingTransform(),
        ]
    )
