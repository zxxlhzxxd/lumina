"""Section visual style model.

Styles cascade: built-in default -> per-type defaults -> per-section overrides.
All fields are optional; unset fields fall back to the next level up.
"""
from __future__ import annotations

from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field, model_validator


BlockAnchor = Literal[
    "top_left",
    "top_center",
    "top_right",
    "middle_left",
    "middle_center",
    "middle_right",
    "bottom_left",
    "bottom_center",
    "bottom_right",
]
VerticalAlign = Literal["top", "middle", "bottom"]


class EdgeInsets(BaseModel):
    """Distance from a block's available area to each slide edge, in inches."""

    top: Optional[float] = Field(default=None, ge=0)
    right: Optional[float] = Field(default=None, ge=0)
    bottom: Optional[float] = Field(default=None, ge=0)
    left: Optional[float] = Field(default=None, ge=0)


class BlockLayout(BaseModel):
    """Optional placement overrides for one semantic slide block."""

    anchor: Optional[BlockAnchor] = None
    margin: Optional[EdgeInsets] = None


class TextStyle(BaseModel):
    font_family: Optional[str] = None
    font_size: Optional[float] = None  # points
    color: Optional[str] = None  # hex e.g. "#FFFFFF"
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    highlight_color: Optional[str] = None  # PowerPoint text highlight
    align: Optional[str] = None  # left | center | right
    vertical_align: Optional[VerticalAlign] = None
    line_spacing: Optional[float] = None


class TextBlockStyle(BaseModel):
    """Text and layout overrides for one semantic slide block."""

    text: Optional[TextStyle] = None
    layout: Optional[BlockLayout] = None


class SectionStyle(BaseModel):
    background_color: Optional[str] = None  # hex
    background_image: Optional[str] = None  # media ref (relative path inside project)
    background_video: Optional[str] = None  # media ref (phase 3)
    body: Optional[TextStyle] = None
    title: Optional[TextStyle] = None
    label: Optional[TextStyle] = None  # 启/应 label styling
    margin: Optional[float] = None  # inches, legacy section-wide safe-area padding
    blocks: Dict[str, TextBlockStyle] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_layout(cls, value):
        """Move the first text-block layout shape into unified block styles."""
        if not isinstance(value, dict):
            return value
        data = dict(value)
        legacy_layout = data.pop("layout", None)
        if not isinstance(legacy_layout, dict):
            return data
        legacy_blocks = legacy_layout.get("blocks")
        if not isinstance(legacy_blocks, dict):
            return data
        blocks = dict(data.get("blocks") or {})
        for block_id, layout in legacy_blocks.items():
            block = dict(blocks.get(block_id) or {})
            block.setdefault("layout", layout)
            blocks[block_id] = block
        data["blocks"] = blocks
        return data
