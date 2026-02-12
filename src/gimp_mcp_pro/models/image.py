"""Image-level models for GIMP MCP Pro."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from gimp_mcp_pro.models.common import Color, FillType, ImageBaseType


class ExportFormat(str, Enum):
    """Supported export formats."""

    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"
    WEBP = "webp"
    PSD = "psd"


class CreateImageParams(BaseModel):
    """Parameters for creating a new image."""

    width: int = Field(..., gt=0, le=32768, description="Image width in pixels")
    height: int = Field(..., gt=0, le=32768, description="Image height in pixels")
    color_mode: ImageBaseType = Field(
        ImageBaseType.RGB, description="Color mode: rgb, grayscale, or indexed"
    )
    fill: FillType = Field(
        FillType.WHITE, description="Initial fill: white, transparent, foreground, background"
    )
    fill_color: Optional[Color] = Field(
        None,
        description="Specific fill color (overrides fill if provided)",
    )


class ExportImageParams(BaseModel):
    """Parameters for exporting an image."""

    file_path: str = Field(
        ..., min_length=1, description="Output file path (extension determines format if format not specified)"
    )
    format: Optional[ExportFormat] = Field(
        None, description="Export format. Auto-detected from file_path extension if not set."
    )
    image_id: Optional[int] = Field(
        None, description="Image to export. Uses active image if not specified."
    )
    quality: int = Field(
        85,
        ge=1,
        le=100,
        description="Quality for lossy formats (JPEG, WebP). 1-100.",
    )
    compression: int = Field(
        9,
        ge=0,
        le=9,
        description="Compression level for PNG. 0 (none) to 9 (max).",
    )

    @field_validator("file_path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("file_path cannot be empty")
        return v


class ImageInfo(BaseModel):
    """Information about an open image."""

    image_id: int = Field(..., description="GIMP internal image ID")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    color_mode: str = Field(..., description="Color mode (RGB, Grayscale, Indexed)")
    precision: str = Field("u8", description="Bit depth / precision")
    num_layers: int = Field(0, description="Number of layers")
    num_channels: int = Field(0, description="Number of custom channels")
    file_path: Optional[str] = Field(None, description="File path if saved")
    file_name: Optional[str] = Field(None, description="File basename")
    is_dirty: bool = Field(False, description="True if image has unsaved changes")
    resolution_x: Optional[float] = Field(None, description="Horizontal resolution (DPI)")
    resolution_y: Optional[float] = Field(None, description="Vertical resolution (DPI)")
    layers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Layer info list (name, visible, opacity, blend_mode, etc.)",
    )
