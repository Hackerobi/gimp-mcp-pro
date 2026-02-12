"""Filter and effects tools for GIMP MCP Pro.

Covers blur, sharpen, noise, edge detection, and artistic effects.
All filters use Gimp.DrawableFilter which wraps GEGL safely in plugin context.
(Direct GEGL graph construction crashes in GIMP 3.0 plugin context.)
"""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge, LONG_TIMEOUT
from gimp_mcp_pro.models.common import OperationResult
from gimp_mcp_pro.utils.errors import GimpCommandError

logger = logging.getLogger("gimp_mcp_pro.tools.filter")


def _filter_preamble(layer_name: str | None, layer_index: int | None) -> list[str]:
    """Standard preamble for filter tools — get image and target drawable."""
    code = [
        "from gi.repository import Gimp, Gegl",
        "images = Gimp.get_images()",
        "if not images: raise RuntimeError('No images are open')",
        "image = images[0]",
    ]
    if layer_name is not None:
        code += [
            f"drawable = image.get_layer_by_name('{layer_name}')",
            f"if drawable is None: raise RuntimeError('Layer \\'{layer_name}\\' not found')",
        ]
    elif layer_index is not None:
        code += [
            "layers = image.get_layers()",
            f"drawable = layers[{layer_index}]",
        ]
    else:
        code += [
            "sel = image.get_selected_layers()",
            "if not sel: raise RuntimeError('No active layer')",
            "drawable = sel[0]",
        ]
    return code


def _apply_drawable_filter(gegl_op: str, props: dict[str, str]) -> list[str]:
    """Generate code to apply a GEGL filter via Gimp.DrawableFilter.

    This is the safe, stable way to apply filters in GIMP 3.0 plugin context.
    The pattern is: create filter → set config props → append → merge.

    Args:
        gegl_op: GEGL operation name (e.g. 'gegl:gaussian-blur')
        props: dict mapping property name to Python expression string
    """
    prop_lines = []
    for k, v in props.items():
        prop_lines.append(f"cfg.set_property('{k}', {v})")

    return [
        f"df = Gimp.DrawableFilter.new(drawable, '{gegl_op}', '')",
        "cfg = df.get_config()",
    ] + prop_lines + [
        "drawable.append_filter(df)",
        "drawable.merge_filter(df)",
        "Gimp.displays_flush()",
    ]


def register_filter_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all filter/effect tools with the MCP server."""

    @mcp.tool()
    def apply_gaussian_blur(
        radius_x: float = 5.0,
        radius_y: float | None = None,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply Gaussian blur to a layer.

        WHEN TO USE: Softening images, creating depth-of-field effects,
        blurring backgrounds, smoothing noise.

        Args:
            radius_x: Horizontal blur radius in pixels (0.0-500.0)
            radius_y: Vertical blur radius. Defaults to radius_x for uniform blur.
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        if radius_y is None:
            radius_y = radius_x

        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter("gegl:gaussian-blur", {
            "std-dev-x": str(radius_x),
            "std-dev-y": str(radius_y),
        })
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_gaussian_blur",
                message=f"Gaussian blur applied (radius {radius_x}x{radius_y})",
                data={"radius_x": radius_x, "radius_y": radius_y},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_gaussian_blur", error=str(e)).model_dump()

    @mcp.tool()
    def apply_unsharp_mask(
        amount: float = 0.5,
        radius: float = 3.0,
        threshold: float = 0.0,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Sharpen a layer using unsharp mask.

        WHEN TO USE: Enhancing image detail, sharpening after resize,
        recovering slightly out-of-focus images.

        Args:
            amount: Sharpening strength (0.0-5.0, typical 0.3-1.0)
            radius: Detail radius in pixels (0.1-120.0, typical 1.0-5.0)
            threshold: Minimum difference threshold (0.0-1.0, higher = less sharpening of subtle detail)
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter("gegl:unsharp-mask", {
            "scale": str(amount),
            "std-dev": str(radius),
            "threshold": str(threshold),
        })
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_unsharp_mask",
                message=f"Unsharp mask applied (amount={amount}, radius={radius})",
                data={"amount": amount, "radius": radius, "threshold": threshold},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_unsharp_mask", error=str(e)).model_dump()

    @mcp.tool()
    def apply_pixelize(
        block_width: int = 10,
        block_height: int | None = None,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply pixelization (mosaic) effect to a layer.

        WHEN TO USE: Censoring faces/text, retro pixel art effect, privacy masking.

        Args:
            block_width: Pixel block width (1-1024)
            block_height: Pixel block height. Defaults to block_width for square blocks.
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        if block_height is None:
            block_height = block_width

        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter("gegl:pixelize", {
            "size-x": str(block_width),
            "size-y": str(block_height),
        })
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_pixelize",
                message=f"Pixelized with {block_width}x{block_height} blocks",
                data={"block_width": block_width, "block_height": block_height},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_pixelize", error=str(e)).model_dump()

    @mcp.tool()
    def apply_edge_detect(
        method: str = "sobel",
        amount: float = 1.0,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply edge detection to a layer.

        WHEN TO USE: Artistic outlines, finding contours, image analysis,
        creating line-art effects.

        Args:
            method: Detection algorithm — "sobel", "prewitt", "laplace"
            amount: Edge detection strength (0.0-10.0)
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        method = method.lower().strip()
        if method == "laplace":
            gegl_op = "gegl:edge-laplace"
            props = {}
        else:
            gegl_op = "gegl:edge"
            props = {"amount": str(amount)}

        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter(gegl_op, props)
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_edge_detect",
                message=f"Edge detection applied ({method})",
                data={"method": method, "amount": amount},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_edge_detect", error=str(e)).model_dump()

    @mcp.tool()
    def apply_emboss(
        azimuth: float = 315.0,
        elevation: float = 45.0,
        depth: int = 2,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply emboss effect to a layer.

        Creates a raised/carved appearance.

        Args:
            azimuth: Light angle in degrees (0-360, default 315 = upper-left)
            elevation: Light elevation in degrees (0-180)
            depth: Emboss depth (1-100)
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter("gegl:emboss", {
            "azimuth": str(azimuth),
            "elevation": str(elevation),
            "depth": str(depth),
        })
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_emboss",
                message=f"Emboss applied (azimuth={azimuth}°, depth={depth})",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_emboss", error=str(e)).model_dump()

    @mcp.tool()
    def apply_noise(
        amount: float = 0.2,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Add random noise to a layer.

        WHEN TO USE: Adding film grain, texture, or breaking up smooth gradients.

        Args:
            amount: Noise intensity (0.0-1.0)
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter("gegl:noise-hsv", {
            "holdness": "2",
            "value-distance": str(amount),
        })
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_noise",
                message=f"Noise added (amount={amount})",
                data={"amount": amount},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_noise", error=str(e)).model_dump()

    @mcp.tool()
    def apply_median(
        radius: int = 3,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply median filter (denoise) to a layer.

        Good for removing salt-and-pepper noise while preserving edges.

        Args:
            radius: Filter radius (1-20)
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        code = _filter_preamble(layer_name, layer_index)
        code += _apply_drawable_filter("gegl:median-blur", {
            "radius": str(radius),
        })
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_median",
                message=f"Median filter applied (radius={radius})",
                data={"radius": radius},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_median", error=str(e)).model_dump()

    @mcp.tool()
    def apply_drop_shadow(
        offset_x: float = 4.0,
        offset_y: float = 4.0,
        blur_radius: float = 8.0,
        color: str = "black",
        opacity: float = 60.0,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply a drop shadow effect to a layer.

        Creates a shadow behind the layer content.

        Args:
            offset_x: Shadow horizontal offset (positive = right)
            offset_y: Shadow vertical offset (positive = down)
            blur_radius: Shadow blur amount
            color: Shadow color (default "black")
            opacity: Shadow opacity 0-100
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        from gimp_mcp_pro.models.common import Color
        c = Color(value=color)

        code = _filter_preamble(layer_name, layer_index) + [
            "pdb = Gimp.get_pdb()",
            "proc = pdb.lookup_procedure('script-fu-drop-shadow')",
            "if not proc: raise RuntimeError('Drop shadow procedure not found')",
            "cfg = proc.create_config()",
            "try: cfg.set_property('image', image)\nexcept: pass",
            "try: cfg.set_property('drawable', drawable)\nexcept: pass",
            f"try: cfg.set_property('offset-x', {offset_x})\nexcept: pass",
            f"try: cfg.set_property('offset-y', {offset_y})\nexcept: pass",
            f"try: cfg.set_property('blur-radius', {blur_radius})\nexcept: pass",
            f"try: cfg.set_property('opacity', {opacity})\nexcept: pass",
            "proc.run(cfg)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="apply_drop_shadow",
                message=f"Drop shadow applied (offset {offset_x},{offset_y}, blur {blur_radius})",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_drop_shadow", error=str(e)).model_dump()
