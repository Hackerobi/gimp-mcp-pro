"""Selection models for GIMP MCP Pro."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from gimp_mcp_pro.models.common import SelectionOp


class SelectRectangleParams(BaseModel):
    """Parameters for rectangular selection."""

    x: float = Field(..., description="Left edge X coordinate")
    y: float = Field(..., description="Top edge Y coordinate")
    width: float = Field(..., gt=0, description="Selection width")
    height: float = Field(..., gt=0, description="Selection height")
    operation: SelectionOp = Field(
        SelectionOp.REPLACE,
        description="How to combine with existing selection",
    )
    feather: bool = Field(False, description="Whether to feather edges")
    feather_radius: float = Field(
        0.0, ge=0, description="Feather radius in pixels"
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )


class SelectEllipseParams(BaseModel):
    """Parameters for elliptical selection."""

    x: float = Field(..., description="Bounding box left edge X")
    y: float = Field(..., description="Bounding box top edge Y")
    width: float = Field(..., gt=0, description="Bounding box width")
    height: float = Field(..., gt=0, description="Bounding box height")
    operation: SelectionOp = Field(
        SelectionOp.REPLACE,
        description="How to combine with existing selection",
    )
    feather: bool = Field(False, description="Whether to feather edges")
    feather_radius: float = Field(
        0.0, ge=0, description="Feather radius in pixels"
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )


class SelectPolygonParams(BaseModel):
    """Parameters for polygon (freeform) selection.

    Points are specified as a flat list of coordinates:
    [x1, y1, x2, y2, x3, y3, ...]

    Minimum 3 points (6 values) required.
    """

    points: list[float] = Field(
        ...,
        min_length=6,
        description="Flat list of polygon vertices: [x1, y1, x2, y2, ...]",
    )
    operation: SelectionOp = Field(
        SelectionOp.REPLACE,
        description="How to combine with existing selection",
    )
    feather: bool = Field(False, description="Whether to feather edges")
    feather_radius: float = Field(
        0.0, ge=0, description="Feather radius in pixels"
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )

    @field_validator("points")
    @classmethod
    def validate_points(cls, v: list[float]) -> list[float]:
        if len(v) % 2 != 0:
            raise ValueError("Points must have an even number of values (x, y pairs)")
        if len(v) < 6:
            raise ValueError("Need at least 3 points (6 values) for a polygon")
        return v


class SelectByColorParams(BaseModel):
    """Parameters for select-by-color."""

    x: float = Field(..., description="Sample point X coordinate")
    y: float = Field(..., description="Sample point Y coordinate")
    threshold: float = Field(
        15.0,
        ge=0.0,
        le=255.0,
        description="Color similarity threshold (0-255)",
    )
    operation: SelectionOp = Field(
        SelectionOp.REPLACE,
        description="How to combine with existing selection",
    )
    sample_merged: bool = Field(
        False,
        description="Sample from merged visible layers instead of active layer",
    )
    image_id: Optional[int] = Field(
        None, description="Target image. Uses active image if not specified."
    )
