"""Mappings from GIMP MCP Pro enums to GIMP 3.0 PyGObject constant names.

These are used when generating Python code to run inside GIMP.
The strings here are the literal Python expressions evaluated in GIMP's context.
"""

from __future__ import annotations

from gimp_mcp_pro.models.common import (
    BlendMode,
    FillType,
    ImageBaseType,
    InterpolationType,
    SelectionOp,
)

# ---------------------------------------------------------------------------
# Selection operations → Gimp.ChannelOps.*
# ---------------------------------------------------------------------------

SELECTION_OP_MAP: dict[SelectionOp, str] = {
    SelectionOp.REPLACE: "Gimp.ChannelOps.REPLACE",
    SelectionOp.ADD: "Gimp.ChannelOps.ADD",
    SelectionOp.SUBTRACT: "Gimp.ChannelOps.SUBTRACT",
    SelectionOp.INTERSECT: "Gimp.ChannelOps.INTERSECT",
}

# ---------------------------------------------------------------------------
# Fill types → Gimp.FillType.*
# ---------------------------------------------------------------------------

FILL_TYPE_MAP: dict[FillType, str] = {
    FillType.FOREGROUND: "Gimp.FillType.FOREGROUND",
    FillType.BACKGROUND: "Gimp.FillType.BACKGROUND",
    FillType.WHITE: "Gimp.FillType.WHITE",
    FillType.TRANSPARENT: "Gimp.FillType.TRANSPARENT",
    FillType.PATTERN: "Gimp.FillType.PATTERN",
}

# ---------------------------------------------------------------------------
# Blend modes → Gimp.LayerMode.*
# ---------------------------------------------------------------------------

BLEND_MODE_MAP: dict[BlendMode, str] = {
    BlendMode.NORMAL: "Gimp.LayerMode.NORMAL",
    BlendMode.DISSOLVE: "Gimp.LayerMode.DISSOLVE",
    BlendMode.MULTIPLY: "Gimp.LayerMode.MULTIPLY",
    BlendMode.SCREEN: "Gimp.LayerMode.SCREEN",
    BlendMode.OVERLAY: "Gimp.LayerMode.OVERLAY",
    BlendMode.SOFT_LIGHT: "Gimp.LayerMode.SOFTLIGHT",
    BlendMode.HARD_LIGHT: "Gimp.LayerMode.HARDLIGHT",
    BlendMode.COLOR_DODGE: "Gimp.LayerMode.DODGE",
    BlendMode.COLOR_BURN: "Gimp.LayerMode.BURN",
    BlendMode.DARKEN_ONLY: "Gimp.LayerMode.DARKEN_ONLY",
    BlendMode.LIGHTEN_ONLY: "Gimp.LayerMode.LIGHTEN_ONLY",
    BlendMode.DIFFERENCE: "Gimp.LayerMode.DIFFERENCE",
    BlendMode.EXCLUSION: "Gimp.LayerMode.EXCLUSION",
    BlendMode.HUE: "Gimp.LayerMode.HSL_COLOR",  # GIMP uses HSL_COLOR for hue
    BlendMode.SATURATION: "Gimp.LayerMode.HSV_SATURATION",
    BlendMode.COLOR: "Gimp.LayerMode.HSL_COLOR",
    BlendMode.LUMINOSITY: "Gimp.LayerMode.LUMINANCE",
    BlendMode.ADDITION: "Gimp.LayerMode.ADDITION",
    BlendMode.SUBTRACT: "Gimp.LayerMode.SUBTRACT",
    BlendMode.GRAIN_EXTRACT: "Gimp.LayerMode.GRAIN_EXTRACT",
    BlendMode.GRAIN_MERGE: "Gimp.LayerMode.GRAIN_MERGE",
    BlendMode.DIVIDE: "Gimp.LayerMode.DIVIDE",
}

# ---------------------------------------------------------------------------
# Image base types → Gimp.ImageBaseType.*
# ---------------------------------------------------------------------------

IMAGE_BASE_TYPE_MAP: dict[ImageBaseType, str] = {
    ImageBaseType.RGB: "Gimp.ImageBaseType.RGB",
    ImageBaseType.GRAYSCALE: "Gimp.ImageBaseType.GRAY",
    ImageBaseType.INDEXED: "Gimp.ImageBaseType.INDEXED",
}

# Image type for layers (with alpha)
IMAGE_TYPE_MAP: dict[tuple[ImageBaseType, bool], str] = {
    (ImageBaseType.RGB, False): "Gimp.ImageType.RGB_IMAGE",
    (ImageBaseType.RGB, True): "Gimp.ImageType.RGBA_IMAGE",
    (ImageBaseType.GRAYSCALE, False): "Gimp.ImageType.GRAY_IMAGE",
    (ImageBaseType.GRAYSCALE, True): "Gimp.ImageType.GRAYA_IMAGE",
    (ImageBaseType.INDEXED, False): "Gimp.ImageType.INDEXED_IMAGE",
    (ImageBaseType.INDEXED, True): "Gimp.ImageType.INDEXEDA_IMAGE",
}

# ---------------------------------------------------------------------------
# Interpolation → Gimp.InterpolationType.*
# ---------------------------------------------------------------------------

INTERPOLATION_MAP: dict[InterpolationType, str] = {
    InterpolationType.NONE: "Gimp.InterpolationType.NONE",
    InterpolationType.LINEAR: "Gimp.InterpolationType.LINEAR",
    InterpolationType.CUBIC: "Gimp.InterpolationType.CUBIC",
    InterpolationType.NOHALO: "Gimp.InterpolationType.NOHALO",
    InterpolationType.LOHALO: "Gimp.InterpolationType.LOHALO",
}
