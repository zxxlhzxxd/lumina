"""Mechanism: ordered composition of text transforms."""

from __future__ import annotations

from typing import Protocol, Sequence, Tuple


class TextTransform(Protocol):
    """A single, named display strategy."""

    name: str

    def apply(self, text: str) -> str:
        ...


class TransformPipeline:
    """Applies display strategies in registration order."""

    def __init__(self, stages: Sequence[TextTransform]) -> None:
        self._stages: Tuple[TextTransform, ...] = tuple(stages)

    @property
    def stages(self) -> Tuple[TextTransform, ...]:
        return self._stages

    def apply(self, text: str) -> str:
        if not text:
            return text
        for stage in self._stages:
            text = stage.apply(text)
        return text
