"""Common models shared across all GIMP MCP Pro tools."""

from __future__ import annotations

import re
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums — mirror GIMP 3.0 constants
# ---------------------------------------------------------------------------


class BlendMode(str, Enum):
    """Layer blend modes available in GIMP 3.0."""

    NORMAL = "normal"
    DISSOLVE = "dissolve"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    SOFT_LIGHT = "soft_light"
    HARD_LIGHT = "hard_light"
    COLOR_DODGE = "color_dodge"
    COLOR_BURN = "color_burn"
    DARKEN_ONLY = "darken_only"
    LIGHTEN_ONLY = "lighten_only"
    DIFFERENCE = "difference"
    EXCLUSION = "exclusion"
    HUE = "hue"
    SATURATION = "saturation"
    COLOR = "color"
    LUMINOSITY = "luminosity"
    ADDITION = "addition"
    SUBTRACT = "subtract"
    GRAIN_EXTRACT = "grain_extract"
    GRAIN_MERGE = "grain_merge"
    DIVIDE = "divide"


class FillType(str, Enum):
    """Fill type for layer creation and fill operations."""

    FOREGROUND = "foreground"
    BACKGROUND = "background"
    WHITE = "white"
    TRANSPARENT = "transparent"
    PATTERN = "pattern"


class SelectionOp(str, Enum):
    """Selection combination operations."""

    REPLACE = "replace"
    ADD = "add"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"


class ImageBaseType(str, Enum):
    """Image color mode."""

    RGB = "rgb"
    GRAYSCALE = "grayscale"
    INDEXED = "indexed"


class ChannelType(str, Enum):
    """Color channel for adjustments."""

    VALUE = "value"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    ALPHA = "alpha"


class InterpolationType(str, Enum):
    """Interpolation method for scaling/transforms."""

    NONE = "none"
    LINEAR = "linear"
    CUBIC = "cubic"
    NOHALO = "nohalo"
    LOHALO = "lohalo"


# ---------------------------------------------------------------------------
# Core value types
# ---------------------------------------------------------------------------

# Regex patterns for color parsing
_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB_COLOR_RE = re.compile(
    r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*(?:,\s*([0-9.]+))?\s*\)$"
)

# Named colors that Gegl.Color.new() accepts
NAMED_COLORS = frozenset(
    {
        "black",
        "white",
        "red",
        "green",
        "blue",
        "yellow",
        "cyan",
        "magenta",
        "orange",
        "purple",
        "pink",
        "brown",
        "gray",
        "grey",
        "transparent",
    }
)


class Color(BaseModel):
    """Color specification.

    Accepts multiple formats:
    - Named colors: "red", "blue", "white", etc.
    - Hex: "#FF0000", "#F00", "#FF000080"
    - RGB: "rgb(255, 0, 0)"
    - RGBA: "rgba(255, 0, 0, 0.5)"

    The value is normalized and validated on construction, but stored
    as-is for maximum compatibility when converting to Gegl.Color calls.
    """

    value: str = Field(
        ...,
        description=(
            "Color as a name ('red'), hex ('#FF0000'), "
            "rgb('rgb(255,0,0)'), or rgba('rgba(255,0,0,0.5)')"
        ),
    )

    @field_validator("value")
    @classmethod
    def validate_color(cls, v: str) -> str:
        v = v.strip()
        low = v.lower()

        # Named color
        if low in NAMED_COLORS:
            return low

        # Hex color
        if _HEX_COLOR_RE.match(v):
            return v

        # rgb()/rgba()
        m = _RGB_COLOR_RE.match(v)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if not all(0 <= c <= 255 for c in (r, g, b)):
                raise ValueError(f"RGB values must be 0-255, got ({r}, {g}, {b})")
            if m.group(4) is not None:
                a = float(m.group(4))
                if not 0.0 <= a <= 1.0:
                    raise ValueError(f"Alpha must be 0.0-1.0, got {a}")
            return v

        raise ValueError(
            f"Invalid color '{v}'. Use a name (red), hex (#FF0000), "
            "rgb(255,0,0), or rgba(255,0,0,0.5)"
        )

    def to_gegl_code(self) -> str:
        """Return Python code to create this color as a Gegl.Color in GIMP."""
        v = self.value
        low = v.lower()

        if low in NAMED_COLORS:
            return f"Gegl.Color.new('{low}')"

        if _HEX_COLOR_RE.match(v):
            return f"Gegl.Color.new('{v}')"

        # For rgb()/rgba(), produce the string form that Gegl.Color.new() accepts
        return f"Gegl.Color.new('{v}')"


class Point(BaseModel):
    """2D coordinate point."""

    x: float = Field(..., description="X coordinate in pixels")
    y: float = Field(..., description="Y coordinate in pixels")


class Region(BaseModel):
    """Rectangular region in an image."""

    x: int = Field(..., ge=0, description="Left edge X coordinate")
    y: int = Field(..., ge=0, description="Top edge Y coordinate")
    width: int = Field(..., gt=0, description="Width in pixels")
    height: int = Field(..., gt=0, description="Height in pixels")


# ---------------------------------------------------------------------------
# Standard operation result
# ---------------------------------------------------------------------------


class OperationResult(BaseModel):
    """Standard response returned by every GIMP MCP Pro tool.

    Tools should always return this structure so AI assistants
    get consistent, predictable responses.
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    operation: str = Field(..., description="Name of the operation performed")
    message: Optional[str] = Field(None, description="Human-readable result message")
    error: Optional[str] = Field(None, description="Error description if success=False")
    data: Optional[dict[str, Any]] = Field(
        None, description="Operation-specific result data"
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp of when the result was produced",
    )

    @classmethod
    def ok(
        cls,
        operation: str,
        message: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> OperationResult:
        """Create a successful result."""
        return cls(success=True, operation=operation, message=message, data=data)

    @classmethod
    def fail(
        cls,
        operation: str,
        error: str,
        data: dict[str, Any] | None = None,
    ) -> OperationResult:
        """Create a failure result."""
        return cls(success=False, operation=operation, error=error, data=data)
