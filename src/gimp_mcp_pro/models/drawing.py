"""Drawing models for GIMP MCP Pro."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from gimp_mcp_pro.models.common import Color, FillType


class FillParams(BaseModel):
    """Parameters for filling the current selection or a region."""

    fill_type: FillType = Field(
        FillType.FOREGROUND,
        description="What to fill with: foreground color, background color, white, transparent, or pattern",
    )
    color: Optional[Color] = Field(
        None,
        description=(
            "Specific color to fill with. If provided, sets the foreground color "
            "first, then fills with foreground."
        ),
    )
    layer_id: Optional[int] = Field(
        None, description="Layer to fill on. Uses active layer if not specified."
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )


class BucketFillParams(BaseModel):
    """Parameters for bucket fill at a point."""

    x: float = Field(..., description="X coordinate to fill from")
    y: float = Field(..., description="Y coordinate to fill from")
    fill_type: FillType = Field(
        FillType.FOREGROUND, description="Fill type"
    )
    color: Optional[Color] = Field(
        None, description="Color to fill with (sets foreground first)"
    )
    threshold: float = Field(
        15.0, ge=0.0, le=255.0, description="Color similarity threshold for fill boundary"
    )
    sample_merged: bool = Field(
        False, description="Sample color from merged visible layers"
    )
    layer_id: Optional[int] = Field(
        None, description="Layer to fill on. Uses active layer if not specified."
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )


class DrawLineParams(BaseModel):
    """Parameters for drawing a straight line."""

    x1: float = Field(..., description="Start X coordinate")
    y1: float = Field(..., description="Start Y coordinate")
    x2: float = Field(..., description="End X coordinate")
    y2: float = Field(..., description="End Y coordinate")
    color: Optional[Color] = Field(
        None, description="Line color (sets foreground color). Uses current foreground if not specified."
    )
    brush_size: float = Field(
        2.0, gt=0, le=1000, description="Brush/line width in pixels"
    )
    layer_id: Optional[int] = Field(
        None, description="Layer to draw on. Uses active layer if not specified."
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )


class BrushStrokeParams(BaseModel):
    """Parameters for a paintbrush or pencil stroke along a path.

    Points are a flat list: [x1, y1, x2, y2, ...]
    """

    points: list[float] = Field(
        ...,
        min_length=4,
        description="Flat list of stroke coordinates: [x1, y1, x2, y2, ...]",
    )
    tool: str = Field(
        "pencil",
        description="Drawing tool: 'pencil' (hard edges) or 'paintbrush' (soft edges)",
    )
    color: Optional[Color] = Field(
        None, description="Stroke color. Uses current foreground if not specified."
    )
    brush_size: float = Field(
        2.0, gt=0, le=1000, description="Brush size in pixels"
    )
    brush_name: Optional[str] = Field(
        None, description="Named brush to use. Uses current brush if not specified."
    )
    layer_id: Optional[int] = Field(
        None, description="Layer to draw on. Uses active layer if not specified."
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )

    @field_validator("points")
    @classmethod
    def validate_points(cls, v: list[float]) -> list[float]:
        if len(v) % 2 != 0:
            raise ValueError("Points must have an even number of values (x, y pairs)")
        if len(v) < 4:
            raise ValueError("Need at least 2 points (4 values) for a stroke")
        return v

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("pencil", "paintbrush"):
            raise ValueError("tool must be 'pencil' or 'paintbrush'")
        return v


class DrawShapeParams(BaseModel):
    """Parameters for drawing a rectangle or ellipse (outline or filled)."""

    shape: str = Field(
        ..., description="Shape type: 'rectangle' or 'ellipse'"
    )
    x: float = Field(..., description="Bounding box left X")
    y: float = Field(..., description="Bounding box top Y")
    width: float = Field(..., gt=0, description="Shape width")
    height: float = Field(..., gt=0, description="Shape height")
    filled: bool = Field(
        True,
        description=(
            "True for filled shape (uses selection + fill), "
            "False for outline only (uses selection + stroke)"
        ),
    )
    color: Optional[Color] = Field(
        None, description="Shape color. Uses current foreground if not specified."
    )
    line_width: float = Field(
        2.0, gt=0, le=100, description="Outline width for non-filled shapes"
    )
    layer_id: Optional[int] = Field(
        None, description="Layer to draw on. Uses active layer if not specified."
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )

    @field_validator("shape")
    @classmethod
    def validate_shape(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("rectangle", "ellipse"):
            raise ValueError("shape must be 'rectangle' or 'ellipse'")
        return v
