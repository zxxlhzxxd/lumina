"""Composable display transforms for verse text.

SQLite keeps the source wording. Callers that present verses (preview, PPTX,
passage API) run the text through a pipeline of strategies.
"""

from app.services.text_transform.base import TextTransform, TransformPipeline
from app.services.text_transform.presets import verse_display_pipeline
from app.services.text_transform.punctuation import PunctuationTransform
from app.services.text_transform.shen_spacing import ShenSpacingTransform

__all__ = [
    "PunctuationTransform",
    "ShenSpacingTransform",
    "TextTransform",
    "TransformPipeline",
    "verse_display_pipeline",
]
