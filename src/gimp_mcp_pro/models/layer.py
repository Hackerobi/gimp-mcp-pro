"""Layer models for GIMP MCP Pro."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from gimp_mcp_pro.models.common import BlendMode, FillType


class CreateLayerParams(BaseModel):
    """Parameters for creating a new layer."""

    name: str = Field(
        "New Layer",
        min_length=1,
        max_length=256,
        description="Layer name",
    )
    width: Optional[int] = Field(
        None,
        gt=0,
        le=32768,
        description="Layer width. Defaults to image width if not specified.",
    )
    height: Optional[int] = Field(
        None,
        gt=0,
        le=32768,
        description="Layer height. Defaults to image height if not specified.",
    )
    opacity: float = Field(
        100.0,
        ge=0.0,
        le=100.0,
        description="Layer opacity (0-100)",
    )
    blend_mode: BlendMode = Field(
        BlendMode.NORMAL,
        description="Layer blend mode",
    )
    fill: FillType = Field(
        FillType.TRANSPARENT,
        description="Initial fill for the layer",
    )
    has_alpha: bool = Field(
        True,
        description="Whether layer should have an alpha channel",
    )
    position: int = Field(
        0,
        ge=0,
        description="Position in layer stack (0 = top)",
    )
    image_id: Optional[int] = Field(
        None,
        description="Target image. Uses active image if not specified.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Layer name cannot be empty")
        return v


class SetLayerPropertyParams(BaseModel):
    """Parameters for setting a single layer property."""

    layer_id: Optional[int] = Field(
        None, description="Layer ID. Uses active layer if not specified."
    )
    layer_name: Optional[str] = Field(
        None, description="Layer name (alternative to layer_id for lookup)."
    )
    image_id: Optional[int] = Field(
        None, description="Image ID. Uses active image if not specified."
    )

    # Only one of these should be set per call
    opacity: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="New opacity (0-100)"
    )
    blend_mode: Optional[BlendMode] = Field(
        None, description="New blend mode"
    )
    visible: Optional[bool] = Field(
        None, description="New visibility state"
    )
    name: Optional[str] = Field(
        None, min_length=1, max_length=256, description="New layer name"
    )
    position: Optional[int] = Field(
        None, ge=0, description="New position in layer stack"
    )


class LayerInfo(BaseModel):
    """Information about a layer."""

    layer_id: int = Field(..., description="GIMP internal layer ID")
    name: str = Field(..., description="Layer name")
    width: int = Field(..., description="Layer width in pixels")
    height: int = Field(..., description="Layer height in pixels")
    offset_x: int = Field(0, description="Layer X offset from image origin")
    offset_y: int = Field(0, description="Layer Y offset from image origin")
    opacity: float = Field(..., description="Layer opacity (0-100)")
    blend_mode: str = Field(..., description="Blend mode name")
    visible: bool = Field(..., description="Whether layer is visible")
    has_alpha: bool = Field(..., description="Whether layer has alpha channel")
    is_group: bool = Field(False, description="Whether this is a layer group")
    parent_id: Optional[int] = Field(None, description="Parent layer group ID")
    children: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Child layers if this is a group",
    )
