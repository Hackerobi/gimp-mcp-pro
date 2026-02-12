"""Layer management tools for GIMP MCP Pro."""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge
from gimp_mcp_pro.models.common import OperationResult
from gimp_mcp_pro.models.layer import CreateLayerParams
from gimp_mcp_pro.utils.errors import GimpCommandError
from gimp_mcp_pro.utils.gimp_constants import BLEND_MODE_MAP, FILL_TYPE_MAP

logger = logging.getLogger("gimp_mcp_pro.tools.layer")


def _layer_lookup_code(layer_name: str | None, layer_index: int | None) -> list[str]:
    """Generate Python code to look up a layer by name or index."""
    code = [
        "images = Gimp.get_images()",
        "if not images: raise RuntimeError('No images are open')",
        "image = images[0]",
    ]
    if layer_name is not None:
        code += [
            f"target = image.get_layer_by_name('{layer_name}')",
            f"if target is None: raise RuntimeError('Layer \\'{layer_name}\\' not found')",
        ]
    elif layer_index is not None:
        code += [
            "layers = image.get_layers()",
            f"if {layer_index} >= len(layers): raise RuntimeError('Layer index {layer_index} out of range')",
            f"target = layers[{layer_index}]",
        ]
    else:
        code += [
            "sel = image.get_selected_layers()",
            "if not sel: raise RuntimeError('No active layer')",
            "target = sel[0]",
        ]
    return code


def register_layer_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all layer management tools with the MCP server."""

    @mcp.tool()
    def create_layer(
        name: str = "New Layer",
        opacity: float = 100.0,
        blend_mode: str = "normal",
        fill: str = "transparent",
        has_alpha: bool = True,
        position: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> dict[str, Any]:
        """Create a new layer in the active image.

        WHEN TO USE: Before drawing new elements. Professional workflows use
        separate layers for background, main subject, details, etc.

        BEST PRACTICE: Create layers BEFORE drawing. Plan your layer structure:
        background -> body -> head -> details -> texture.

        Args:
            name: Layer name (e.g., "Background", "Eyes", "Shadow")
            opacity: Layer opacity 0-100 (100 = fully opaque)
            blend_mode: Blend mode — "normal", "multiply", "screen", "overlay", etc.
            fill: Initial fill — "transparent", "white", "foreground", "background"
            has_alpha: Whether layer has transparency (usually True)
            position: Stack position (0 = top of stack)
            width: Layer width (defaults to image width)
            height: Layer height (defaults to image height)

        Returns:
            Operation result with layer info.
        """
        params = CreateLayerParams(
            name=name, opacity=opacity, blend_mode=blend_mode,
            fill=fill, has_alpha=has_alpha, position=position,
            width=width, height=height,
        )
        mode_expr = BLEND_MODE_MAP.get(params.blend_mode, "Gimp.LayerMode.NORMAL")
        fill_expr = FILL_TYPE_MAP.get(params.fill, "Gimp.FillType.TRANSPARENT")
        img_type = "Gimp.ImageType.RGBA_IMAGE" if params.has_alpha else "Gimp.ImageType.RGB_IMAGE"
        w = f"{params.width}" if params.width else "image.get_width()"
        h = f"{params.height}" if params.height else "image.get_height()"

        code = [
            "from gi.repository import Gimp, Gegl",
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open in GIMP')",
            "image = images[0]",
            f"layer = Gimp.Layer.new(image, '{params.name}', {w}, {h}, "
            f"{img_type}, {params.opacity}, {mode_expr})",
            f"image.insert_layer(layer, None, {params.position})",
            f"Gimp.Drawable.edit_fill(layer, {fill_expr})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="create_layer",
                message=f"Created layer '{params.name}'",
                data={"name": params.name, "opacity": params.opacity,
                      "blend_mode": params.blend_mode.value, "position": params.position},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="create_layer", error=str(e)).model_dump()

    @mcp.tool()
    def list_layers() -> dict[str, Any]:
        """List all layers in the active image with their properties.

        WHEN TO USE: Before drawing (to find the right layer), when debugging
        visual issues, or to understand image structure.

        Returns:
            Layer list with name, visibility, opacity, blend mode, dimensions.
        """
        code = [
            "import json",
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            "layers = image.get_layers()",
            "result = []",
            "for i, layer in enumerate(layers):\n"
            "    info = {'index': i, 'name': layer.get_name(), 'visible': layer.get_visible(),\n"
            "            'opacity': layer.get_opacity(), 'width': layer.get_width(),\n"
            "            'height': layer.get_height(), 'has_alpha': layer.has_alpha()}\n"
            "    try: info['blend_mode'] = str(layer.get_mode())\n"
            "    except: info['blend_mode'] = 'unknown'\n"
            "    result.append(info)",
            "print(json.dumps(result))",
        ]
        try:
            result = bridge.execute_python(code)
            import json as _json
            layers_data = []
            for out in result.get("results", []):
                if out and out.strip():
                    try:
                        layers_data = _json.loads(out.strip())
                        break
                    except _json.JSONDecodeError:
                        continue
            return OperationResult.ok(
                operation="list_layers",
                message=f"Found {len(layers_data)} layer(s)",
                data={"layers": layers_data, "count": len(layers_data)},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="list_layers", error=str(e)).model_dump()

    @mcp.tool()
    def set_active_layer(
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Set which layer is active (the one drawing tools operate on).

        WHEN TO USE: Before any drawing or editing operation, switch to the
        correct layer. Drawing on the wrong layer is the most common mistake.

        Args:
            layer_name: Layer name to activate (e.g., "Background")
            layer_index: Layer index (0 = topmost). Alternative to name.
        """
        if layer_name is None and layer_index is None:
            return OperationResult.fail(
                operation="set_active_layer",
                error="Must specify either layer_name or layer_index",
            ).model_dump()

        code = _layer_lookup_code(layer_name, layer_index) + [
            "image.set_selected_layers([target])",
            "Gimp.displays_flush()",
            "print(target.get_name())",
        ]
        try:
            result = bridge.execute_python(code)
            name = ""
            for out in result.get("results", []):
                if out and out.strip():
                    name = out.strip()
            return OperationResult.ok(
                operation="set_active_layer",
                message=f"Active layer set to '{name}'",
                data={"layer_name": name},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="set_active_layer", error=str(e)).model_dump()

    @mcp.tool()
    def delete_layer(
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Delete a layer from the active image.

        Args:
            layer_name: Name of layer to delete.
            layer_index: Index of layer to delete (0 = topmost).
        """
        if layer_name is None and layer_index is None:
            return OperationResult.fail(
                operation="delete_layer", error="Must specify layer_name or layer_index"
            ).model_dump()

        code = _layer_lookup_code(layer_name, layer_index) + [
            "name = target.get_name()",
            "image.remove_layer(target)",
            "Gimp.displays_flush()",
            "print(name)",
        ]
        try:
            result = bridge.execute_python(code)
            return OperationResult.ok(operation="delete_layer", message="Layer deleted").model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="delete_layer", error=str(e)).model_dump()

    @mcp.tool()
    def set_layer_opacity(
        opacity: float,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Set a layer's opacity.

        Args:
            opacity: Opacity 0-100 (0 = fully transparent, 100 = fully opaque)
            layer_name: Target layer by name.
            layer_index: Target layer by index. Uses active layer if neither specified.
        """
        if not 0.0 <= opacity <= 100.0:
            return OperationResult.fail(
                operation="set_layer_opacity", error=f"Opacity must be 0-100, got {opacity}"
            ).model_dump()

        code = _layer_lookup_code(layer_name, layer_index) + [
            f"target.set_opacity({opacity})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="set_layer_opacity",
                message=f"Layer opacity set to {opacity}%",
                data={"opacity": opacity},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="set_layer_opacity", error=str(e)).model_dump()

    @mcp.tool()
    def set_layer_visibility(
        visible: bool,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Show or hide a layer.

        Args:
            visible: True to show, False to hide.
            layer_name: Target layer by name.
            layer_index: Target layer by index. Uses active layer if neither specified.
        """
        code = _layer_lookup_code(layer_name, layer_index) + [
            f"target.set_visible({visible})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            state = "visible" if visible else "hidden"
            return OperationResult.ok(
                operation="set_layer_visibility",
                message=f"Layer is now {state}",
                data={"visible": visible},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="set_layer_visibility", error=str(e)).model_dump()

    @mcp.tool()
    def duplicate_layer(
        layer_name: str | None = None,
        layer_index: int | None = None,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """Duplicate a layer.

        Args:
            layer_name: Source layer name.
            layer_index: Source layer index. Uses active layer if neither specified.
            new_name: Name for the duplicate. Defaults to "Copy of <original>".
        """
        code = _layer_lookup_code(layer_name, layer_index) + [
            "dup = target.copy()",
        ]
        if new_name:
            code.append(f"dup.set_name('{new_name}')")
        else:
            code.append("dup.set_name('Copy of ' + target.get_name())")
        code += [
            "image.insert_layer(dup, None, 0)",
            "Gimp.displays_flush()",
            "print(dup.get_name())",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(operation="duplicate_layer", message="Layer duplicated").model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="duplicate_layer", error=str(e)).model_dump()

    @mcp.tool()
    def merge_visible_layers() -> dict[str, Any]:
        """Merge all visible layers into one.

        WHEN TO USE: Consolidate visible work while preserving hidden layers.
        WARNING: Destructive operation — consider using undo groups.
        """
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            "image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="merge_visible_layers", message="Visible layers merged"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="merge_visible_layers", error=str(e)).model_dump()

    @mcp.tool()
    def add_alpha_channel(
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Add an alpha (transparency) channel to a layer.

        WHEN TO USE: Before using transparent fills or edit_clear on a layer
        that was created without alpha (e.g., the default Background layer).

        Args:
            layer_name: Target layer by name.
            layer_index: Target layer by index. Uses active layer if neither specified.
        """
        code = _layer_lookup_code(layer_name, layer_index) + [
            "if not target.has_alpha():\n    target.add_alpha()",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="add_alpha_channel", message="Alpha channel added"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="add_alpha_channel", error=str(e)).model_dump()
