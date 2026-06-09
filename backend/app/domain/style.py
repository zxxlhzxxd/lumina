"""Section/Theme visual style model.

Styles cascade: Theme defaults -> per-type defaults -> per-section overrides.
All fields are optional; unset fields fall back to the next level up.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TextStyle(BaseModel):
    font_family: Optional[str] = None
    font_size: Optional[float] = None  # points
    color: Optional[str] = None  # hex e.g. "#FFFFFF"
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    align: Optional[str] = None  # left | center | right
    line_spacing: Optional[float] = None


class SectionStyle(BaseModel):
    background_color: Optional[str] = None  # hex
    background_image: Optional[str] = None  # media ref (relative path inside project)
    background_video: Optional[str] = None  # media ref (phase 3)
    body: Optional[TextStyle] = None
    title: Optional[TextStyle] = None
    label: Optional[TextStyle] = None  # 启/应 label styling
    margin: Optional[float] = None  # inches, safe-area padding
