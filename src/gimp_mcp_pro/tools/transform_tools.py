"""Transform tools for GIMP MCP Pro.

Covers scaling, rotation, flipping, cropping, and perspective transforms
for both images and individual layers.
"""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge, LONG_TIMEOUT
from gimp_mcp_pro.models.common import OperationResult
from gimp_mcp_pro.utils.errors import GimpCommandError

logger = logging.getLogger("gimp_mcp_pro.tools.transform")


def _img_preamble() -> list[str]:
    """Standard preamble to get active image."""
    return [
        "from gi.repository import Gimp, Gegl",
        "images = Gimp.get_images()",
        "if not images: raise RuntimeError('No images are open')",
        "image = images[0]",
    ]


def _layer_target(layer_name: str | None, layer_index: int | None) -> list[str]:
    """Code to resolve a layer target."""
    if layer_name is not None:
        return [
            f"target = image.get_layer_by_name('{layer_name}')",
            f"if target is None: raise RuntimeError('Layer \\'{layer_name}\\' not found')",
        ]
    elif layer_index is not None:
        return [
            "layers = image.get_layers()",
            f"if {layer_index} >= len(layers): raise RuntimeError('Layer index out of range')",
            f"target = layers[{layer_index}]",
        ]
    else:
        return [
            "sel = image.get_selected_layers()",
            "if not sel: raise RuntimeError('No active layer')",
            "target = sel[0]",
        ]


def register_transform_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all transform tools with the MCP server."""

    @mcp.tool()
    def scale_image(
        new_width: int,
        new_height: int,
        interpolation: str = "cubic",
    ) -> dict[str, Any]:
        """Scale the entire image (all layers) to new dimensions.

        WHEN TO USE: Resizing the final image for output, or changing
        overall canvas dimensions while scaling content.

        Args:
            new_width: Target width in pixels (1-32768)
            new_height: Target height in pixels (1-32768)
            interpolation: Quality — "none", "linear", "cubic" (recommended),
                          "nohalo", "lohalo"
        """
        if new_width < 1 or new_width > 32768 or new_height < 1 or new_height > 32768:
            return OperationResult.fail(
                operation="scale_image",
                error=f"Dimensions must be 1-32768, got {new_width}x{new_height}",
            ).model_dump()

        interp_map = {
            "none": "Gimp.InterpolationType.NONE",
            "linear": "Gimp.InterpolationType.LINEAR",
            "cubic": "Gimp.InterpolationType.CUBIC",
            "nohalo": "Gimp.InterpolationType.NOHALO",
            "lohalo": "Gimp.InterpolationType.LOHALO",
        }
        interp_expr = interp_map.get(interpolation.lower(), "Gimp.InterpolationType.CUBIC")

        code = _img_preamble() + [
            f"Gimp.context_set_interpolation({interp_expr})",
            f"image.scale({new_width}, {new_height})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="scale_image",
                message=f"Image scaled to {new_width}x{new_height}",
                data={"width": new_width, "height": new_height},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="scale_image", error=str(e)).model_dump()

    @mcp.tool()
    def scale_layer(
        new_width: int,
        new_height: int,
        interpolation: str = "cubic",
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Scale a single layer to new dimensions.

        NOTE: This changes the layer's pixel content, not the canvas.
        The layer may become larger or smaller than the image canvas.

        Args:
            new_width: Target width in pixels
            new_height: Target height in pixels
            interpolation: "none", "linear", "cubic", "nohalo", "lohalo"
            layer_name: Target layer by name. Uses active layer if neither specified.
            layer_index: Target layer by index.
        """
        interp_map = {
            "none": "Gimp.InterpolationType.NONE",
            "linear": "Gimp.InterpolationType.LINEAR",
            "cubic": "Gimp.InterpolationType.CUBIC",
            "nohalo": "Gimp.InterpolationType.NOHALO",
            "lohalo": "Gimp.InterpolationType.LOHALO",
        }
        interp_expr = interp_map.get(interpolation.lower(), "Gimp.InterpolationType.CUBIC")

        code = _img_preamble() + _layer_target(layer_name, layer_index) + [
            f"Gimp.context_set_interpolation({interp_expr})",
            f"target.scale({new_width}, {new_height}, True)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="scale_layer",
                message=f"Layer scaled to {new_width}x{new_height}",
                data={"width": new_width, "height": new_height},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="scale_layer", error=str(e)).model_dump()

    @mcp.tool()
    def rotate_image(angle: int) -> dict[str, Any]:
        """Rotate the entire image by 90, 180, or 270 degrees.

        Args:
            angle: Rotation angle — must be 90, 180, or 270.
        """
        rotation_map = {
            90: "Gimp.RotationType.DEGREES90",
            180: "Gimp.RotationType.DEGREES180",
            270: "Gimp.RotationType.DEGREES270",
        }
        if angle not in rotation_map:
            return OperationResult.fail(
                operation="rotate_image",
                error=f"angle must be 90, 180, or 270 (got {angle})",
            ).model_dump()

        code = _img_preamble() + [
            f"image.rotate({rotation_map[angle]})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="rotate_image",
                message=f"Image rotated {angle}°",
                data={"angle": angle},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="rotate_image", error=str(e)).model_dump()

    @mcp.tool()
    def rotate_layer(
        angle_degrees: float,
        auto_resize: bool = True,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Rotate a layer by an arbitrary angle.

        Args:
            angle_degrees: Rotation angle in degrees (positive = counter-clockwise)
            auto_resize: If True, resize layer to fit rotated content
            layer_name: Target layer by name.
            layer_index: Target layer by index. Uses active layer if neither specified.
        """
        import math
        angle_rad = math.radians(angle_degrees)

        code = _img_preamble() + _layer_target(layer_name, layer_index) + [
            "import math",
            f"angle_rad = {angle_rad}",
            "off = target.get_offsets()",
            "cx = off.offset_x + target.get_width() / 2.0",
            "cy = off.offset_y + target.get_height() / 2.0",
            f"Gimp.Item.transform_rotate(target, angle_rad, {'True' if auto_resize else 'False'}, cx, cy)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="rotate_layer",
                message=f"Layer rotated {angle_degrees}°",
                data={"angle_degrees": angle_degrees},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="rotate_layer", error=str(e)).model_dump()

    @mcp.tool()
    def flip_image(direction: str = "horizontal") -> dict[str, Any]:
        """Flip the entire image.

        Args:
            direction: "horizontal" (mirror left/right) or "vertical" (mirror top/bottom)
        """
        direction = direction.lower().strip()
        if direction not in ("horizontal", "vertical"):
            return OperationResult.fail(
                operation="flip_image",
                error="direction must be 'horizontal' or 'vertical'",
            ).model_dump()

        flip_type = "Gimp.OrientationType.HORIZONTAL" if direction == "horizontal" else "Gimp.OrientationType.VERTICAL"
        code = _img_preamble() + [
            f"image.flip({flip_type})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="flip_image",
                message=f"Image flipped {direction}",
                data={"direction": direction},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="flip_image", error=str(e)).model_dump()

    @mcp.tool()
    def flip_layer(
        direction: str = "horizontal",
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Flip a single layer.

        Args:
            direction: "horizontal" or "vertical"
            layer_name: Target layer by name.
            layer_index: Target layer by index. Uses active layer if neither specified.
        """
        direction = direction.lower().strip()
        if direction not in ("horizontal", "vertical"):
            return OperationResult.fail(
                operation="flip_layer", error="direction must be 'horizontal' or 'vertical'"
            ).model_dump()

        flip_type = "Gimp.OrientationType.HORIZONTAL" if direction == "horizontal" else "Gimp.OrientationType.VERTICAL"
        auto_center = "target.get_width() / 2.0" if direction == "horizontal" else "target.get_height() / 2.0"

        code = _img_preamble() + _layer_target(layer_name, layer_index) + [
            f"Gimp.Item.transform_flip_simple(target, {flip_type}, True, 0)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="flip_layer",
                message=f"Layer flipped {direction}",
                data={"direction": direction},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="flip_layer", error=str(e)).model_dump()

    @mcp.tool()
    def crop_to_selection() -> dict[str, Any]:
        """Crop the image to the current selection bounds.

        WHEN TO USE: After making a selection around the area you want to keep.
        The image canvas will be resized to fit the selection.
        """
        code = _img_preamble() + [
            "bounds = Gimp.Selection.bounds(image)",
            "if not bounds.non_empty: raise RuntimeError('No selection — select an area first')",
            "image.crop(bounds.x2 - bounds.x1, bounds.y2 - bounds.y1, bounds.x1, bounds.y1)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="crop_to_selection", message="Image cropped to selection"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="crop_to_selection", error=str(e)).model_dump()

    @mcp.tool()
    def crop_image(
        x: int, y: int, width: int, height: int,
    ) -> dict[str, Any]:
        """Crop the image to a specific rectangle.

        Args:
            x: Left edge X coordinate
            y: Top edge Y coordinate
            width: Crop width in pixels
            height: Crop height in pixels
        """
        if width < 1 or height < 1:
            return OperationResult.fail(
                operation="crop_image", error="width and height must be >= 1"
            ).model_dump()

        code = _img_preamble() + [
            f"image.crop({width}, {height}, {x}, {y})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="crop_image",
                message=f"Image cropped to {width}x{height} at ({x},{y})",
                data={"x": x, "y": y, "width": width, "height": height},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="crop_image", error=str(e)).model_dump()

    @mcp.tool()
    def autocrop_image() -> dict[str, Any]:
        """Automatically crop the image to remove border whitespace/transparency.

        WHEN TO USE: After drawing, to trim unused canvas around the content.
        """
        code = _img_preamble() + [
            "pdb = Gimp.get_pdb()",
            "proc = pdb.lookup_procedure('gimp-image-autocrop')",
            "if not proc: raise RuntimeError('Autocrop procedure not found')",
            "cfg = proc.create_config()",
            "cfg.set_property('image', image)",
            "sel = image.get_selected_layers()\nif sel:\n    try: cfg.set_property('drawable', sel[0])\n    except: pass",
            "proc.run(cfg)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="autocrop_image", message="Image auto-cropped"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="autocrop_image", error=str(e)).model_dump()

    @mcp.tool()
    def resize_canvas(
        new_width: int,
        new_height: int,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> dict[str, Any]:
        """Resize the image canvas without scaling content.

        Content stays the same size; canvas grows or shrinks around it.
        Use offsets to position existing content within the new canvas.

        Args:
            new_width: New canvas width
            new_height: New canvas height
            offset_x: Horizontal offset for existing content (can be negative)
            offset_y: Vertical offset for existing content (can be negative)
        """
        code = _img_preamble() + [
            f"image.resize({new_width}, {new_height}, {offset_x}, {offset_y})",
            "# Resize all layers to canvas",
            "for layer in image.get_layers():\n    layer.resize_to_image_size()",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="resize_canvas",
                message=f"Canvas resized to {new_width}x{new_height}",
                data={"width": new_width, "height": new_height,
                      "offset_x": offset_x, "offset_y": offset_y},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="resize_canvas", error=str(e)).model_dump()

    @mcp.tool()
    def offset_layer(
        offset_x: int,
        offset_y: int,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Move a layer by an offset (reposition within the canvas).

        Args:
            offset_x: Horizontal offset in pixels (positive = right)
            offset_y: Vertical offset in pixels (positive = down)
            layer_name: Target layer by name.
            layer_index: Target layer by index. Uses active layer if neither specified.
        """
        code = _img_preamble() + _layer_target(layer_name, layer_index) + [
            f"target.set_offsets(target.get_offsets().offset_x + {offset_x}, "
            f"target.get_offsets().offset_y + {offset_y})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="offset_layer",
                message=f"Layer moved by ({offset_x}, {offset_y})",
                data={"offset_x": offset_x, "offset_y": offset_y},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="offset_layer", error=str(e)).model_dump()
