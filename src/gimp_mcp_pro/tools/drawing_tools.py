"""Drawing tools for GIMP MCP Pro."""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge
from gimp_mcp_pro.models.common import Color, FillType, OperationResult
from gimp_mcp_pro.utils.errors import GimpCommandError
from gimp_mcp_pro.utils.gimp_constants import FILL_TYPE_MAP, SELECTION_OP_MAP

logger = logging.getLogger("gimp_mcp_pro.tools.drawing")


def _set_color_code(color: Color | None, target: str = "foreground") -> list[str]:
    """Generate code to set foreground or background color."""
    if color is None:
        return []
    gegl_expr = color.to_gegl_code()
    if target == "foreground":
        return [
            "from gi.repository import Gegl",
            f"_color = {gegl_expr}",
            "Gimp.context_set_foreground(_color)",
        ]
    else:
        return [
            "from gi.repository import Gegl",
            f"_color = {gegl_expr}",
            "Gimp.context_set_background(_color)",
        ]


def _get_drawable_code() -> list[str]:
    """Generate code to get the current drawable."""
    return [
        "images = Gimp.get_images()",
        "if not images: raise RuntimeError('No images are open')",
        "image = images[0]",
        "sel = image.get_selected_layers()",
        "if not sel: raise RuntimeError('No active layer')",
        "drawable = sel[0]",
    ]


def register_drawing_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all drawing tools with the MCP server."""

    @mcp.tool()
    def set_foreground_color(color: str) -> dict[str, Any]:
        """Set the foreground color used for drawing operations.

        WHEN TO USE: Before any drawing, fill, or stroke operation that
        uses the foreground color.

        Args:
            color: Color as name ("red"), hex ("#FF0000"), or rgb("rgb(255,0,0)")
        """
        c = Color(value=color)
        code = [
            "from gi.repository import Gimp, Gegl",
            f"_color = {c.to_gegl_code()}",
            "Gimp.context_set_foreground(_color)",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="set_foreground_color",
                message=f"Foreground color set to {color}",
                data={"color": color},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="set_foreground_color", error=str(e)).model_dump()

    @mcp.tool()
    def set_background_color(color: str) -> dict[str, Any]:
        """Set the background color.

        Args:
            color: Color as name ("white"), hex ("#FFFFFF"), or rgb("rgb(255,255,255)")
        """
        c = Color(value=color)
        code = [
            "from gi.repository import Gimp, Gegl",
            f"_color = {c.to_gegl_code()}",
            "Gimp.context_set_background(_color)",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="set_background_color",
                message=f"Background color set to {color}",
                data={"color": color},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="set_background_color", error=str(e)).model_dump()

    @mcp.tool()
    def fill_selection(
        fill_type: str = "foreground",
        color: str | None = None,
    ) -> dict[str, Any]:
        """Fill the current selection (or entire layer if no selection) with color.

        WHEN TO USE: After creating a selection (rectangle, ellipse, polygon),
        fill it with a color to create shapes.

        BEST PRACTICE (from maorcc):
        - Use polygon selection + fill for solid shapes (NOT paintbrush)
        - Always clear selection after filling: select_none is called for you
        - Avoid feathering unless you specifically want soft edges

        Args:
            fill_type: "foreground", "background", "white", "transparent", or "pattern"
            color: Optional color to set before filling (sets foreground color).
                   Uses current foreground if not specified.
        """
        fill_expr = FILL_TYPE_MAP.get(FillType(fill_type), "Gimp.FillType.FOREGROUND")
        code = ["from gi.repository import Gimp, Gegl"]

        if color:
            c = Color(value=color)
            code += [
                f"_color = {c.to_gegl_code()}",
                "Gimp.context_set_foreground(_color)",
            ]

        code += _get_drawable_code() + [
            f"Gimp.Drawable.edit_fill(drawable, {fill_expr})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="fill_selection",
                message=f"Filled with {fill_type}" + (f" ({color})" if color else ""),
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="fill_selection", error=str(e)).model_dump()

    @mcp.tool()
    def draw_line(
        x1: float, y1: float,
        x2: float, y2: float,
        color: str | None = None,
        brush_size: float = 2.0,
    ) -> dict[str, Any]:
        """Draw a straight line between two points.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            color: Line color. Uses current foreground if not specified.
            brush_size: Line width in pixels (default 2.0)
        """
        code = ["from gi.repository import Gimp, Gegl"]
        if color:
            c = Color(value=color)
            code += [f"Gimp.context_set_foreground({c.to_gegl_code()})"]

        code += _get_drawable_code() + [
            f"Gimp.context_set_brush_size({brush_size})",
            f"Gimp.pencil(drawable, [{x1}, {y1}, {x2}, {y2}])",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="draw_line",
                message=f"Drew line from ({x1},{y1}) to ({x2},{y2})",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="draw_line", error=str(e)).model_dump()

    @mcp.tool()
    def draw_brush_stroke(
        points: list[float],
        tool: str = "pencil",
        color: str | None = None,
        brush_size: float = 2.0,
    ) -> dict[str, Any]:
        """Draw a stroke along a series of points.

        Use 'pencil' for hard-edged lines, 'paintbrush' for soft brush strokes.

        NOTE: For filling shapes, do NOT use brush strokes — use polygon
        selection + fill_selection instead. Brush strokes create outlines only.

        Args:
            points: Flat list of coordinates [x1, y1, x2, y2, x3, y3, ...]
            tool: "pencil" (hard edge) or "paintbrush" (soft)
            color: Stroke color. Uses current foreground if not specified.
            brush_size: Brush width in pixels
        """
        if len(points) < 4 or len(points) % 2 != 0:
            return OperationResult.fail(
                operation="draw_brush_stroke",
                error="points must have at least 4 values and an even count",
            ).model_dump()

        code = ["from gi.repository import Gimp, Gegl"]
        if color:
            c = Color(value=color)
            code += [f"Gimp.context_set_foreground({c.to_gegl_code()})"]

        code += _get_drawable_code() + [
            f"Gimp.context_set_brush_size({brush_size})",
        ]

        points_str = str(points)
        if tool == "paintbrush":
            code.append(f"Gimp.paintbrush_default(drawable, {points_str})")
        else:
            code.append(f"Gimp.pencil(drawable, {points_str})")

        code.append("Gimp.displays_flush()")

        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="draw_brush_stroke",
                message=f"Drew {tool} stroke with {len(points) // 2} points",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="draw_brush_stroke", error=str(e)).model_dump()

    @mcp.tool()
    def draw_rectangle(
        x: float, y: float,
        width: float, height: float,
        filled: bool = True,
        color: str | None = None,
        line_width: float = 2.0,
    ) -> dict[str, Any]:
        """Draw a rectangle (filled or outline only).

        BEST PRACTICE: Uses selection + fill for filled rectangles (not brush).
        This produces clean, solid shapes.

        Args:
            x, y: Top-left corner coordinates
            width, height: Rectangle dimensions
            filled: True for solid fill, False for outline only
            color: Shape color. Uses current foreground if not specified.
            line_width: Outline width for non-filled rectangles
        """
        code = ["from gi.repository import Gimp, Gegl"]
        if color:
            c = Color(value=color)
            code += [f"Gimp.context_set_foreground({c.to_gegl_code()})"]

        code += _get_drawable_code() + [
            f"Gimp.Image.select_rectangle(image, Gimp.ChannelOps.REPLACE, {x}, {y}, {width}, {height})",
        ]

        if filled:
            code += [
                "Gimp.Drawable.edit_fill(drawable, Gimp.FillType.FOREGROUND)",
            ]
        else:
            code += [
                f"Gimp.context_set_line_width({line_width})",
                "Gimp.Drawable.edit_stroke_selection(drawable)",
            ]

        code += [
            "Gimp.Selection.none(image)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            mode = "filled" if filled else "outline"
            return OperationResult.ok(
                operation="draw_rectangle",
                message=f"Drew {mode} rectangle at ({x},{y}) size {width}x{height}",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="draw_rectangle", error=str(e)).model_dump()

    @mcp.tool()
    def draw_ellipse(
        x: float, y: float,
        width: float, height: float,
        filled: bool = True,
        color: str | None = None,
        line_width: float = 2.0,
    ) -> dict[str, Any]:
        """Draw an ellipse/circle (filled or outline only).

        For a circle, set width == height.

        Args:
            x, y: Bounding box top-left corner
            width, height: Bounding box dimensions
            filled: True for solid fill, False for outline only
            color: Shape color. Uses current foreground if not specified.
            line_width: Outline width for non-filled ellipses
        """
        code = ["from gi.repository import Gimp, Gegl"]
        if color:
            c = Color(value=color)
            code += [f"Gimp.context_set_foreground({c.to_gegl_code()})"]

        code += _get_drawable_code() + [
            f"Gimp.Image.select_ellipse(image, Gimp.ChannelOps.REPLACE, {x}, {y}, {width}, {height})",
        ]

        if filled:
            code += ["Gimp.Drawable.edit_fill(drawable, Gimp.FillType.FOREGROUND)"]
        else:
            code += [
                f"Gimp.context_set_line_width({line_width})",
                "Gimp.Drawable.edit_stroke_selection(drawable)",
            ]

        code += [
            "Gimp.Selection.none(image)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            mode = "filled" if filled else "outline"
            return OperationResult.ok(
                operation="draw_ellipse",
                message=f"Drew {mode} ellipse at ({x},{y}) size {width}x{height}",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="draw_ellipse", error=str(e)).model_dump()

    @mcp.tool()
    def draw_polygon(
        points: list[float],
        filled: bool = True,
        color: str | None = None,
        line_width: float = 2.0,
    ) -> dict[str, Any]:
        """Draw a polygon (filled or outline).

        BEST PRACTICE: This is THE correct way to draw filled shapes in GIMP.
        Uses polygon selection + fill, producing clean solid shapes.

        Args:
            points: Flat list of vertex coordinates [x1,y1, x2,y2, x3,y3, ...]
                    Minimum 3 vertices (6 values).
            filled: True for solid fill, False for outline only
            color: Shape color. Uses current foreground if not specified.
            line_width: Outline width for non-filled polygons
        """
        if len(points) < 6 or len(points) % 2 != 0:
            return OperationResult.fail(
                operation="draw_polygon",
                error="Need at least 3 points (6 values) with even count",
            ).model_dump()

        code = ["from gi.repository import Gimp, Gegl"]
        if color:
            c = Color(value=color)
            code += [f"Gimp.context_set_foreground({c.to_gegl_code()})"]

        code += _get_drawable_code() + [
            f"Gimp.Image.select_polygon(image, Gimp.ChannelOps.REPLACE, {points})",
        ]

        if filled:
            code += ["Gimp.Drawable.edit_fill(drawable, Gimp.FillType.FOREGROUND)"]
        else:
            code += [
                f"Gimp.context_set_line_width({line_width})",
                "Gimp.Drawable.edit_stroke_selection(drawable)",
            ]

        code += [
            "Gimp.Selection.none(image)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            n_verts = len(points) // 2
            mode = "filled" if filled else "outline"
            return OperationResult.ok(
                operation="draw_polygon",
                message=f"Drew {mode} polygon with {n_verts} vertices",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="draw_polygon", error=str(e)).model_dump()

    @mcp.tool()
    def add_text(
        text: str,
        x: float = 0.0,
        y: float = 0.0,
        font_name: str = "Sans",
        font_size: float = 24.0,
        color: str | None = None,
        layer_name: str = "Text",
    ) -> dict[str, Any]:
        """Add a text layer to the image.

        Creates a new floating text layer at the specified position.

        Args:
            text: The text content to add.
            x: X position for text placement.
            y: Y position for text placement.
            font_name: Font name (e.g., "Sans", "Serif", "Monospace").
            font_size: Font size in pixels.
            color: Text color. Uses current foreground if not specified.
            layer_name: Name for the text layer.
        """
        code = ["from gi.repository import Gimp, Gegl"]
        if color:
            c = Color(value=color)
            code += [f"Gimp.context_set_foreground({c.to_gegl_code()})"]

        # Escape text for Python string
        escaped_text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

        # Map common font names to GIMP 3.0 font names
        font_map = {
            "sans": "Sans-serif", "sans-serif": "Sans-serif",
            "serif": "Serif", "mono": "Monospace", "monospace": "Monospace",
        }
        resolved_font = font_map.get(font_name.lower(), font_name)

        code += [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            f"font = Gimp.Font.get_by_name('{resolved_font}')",
            "if font is None: font = Gimp.context_get_font()",
            "unit = Gimp.Unit.pixel()",
            f"text_layer = Gimp.TextLayer.new(image, '{escaped_text}', font, {font_size}, unit)",
            "image.insert_layer(text_layer, None, 0)",
            f"text_layer.set_offsets({int(x)}, {int(y)})",
            f"text_layer.set_name('{layer_name}')",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="add_text",
                message=f"Text layer added: \"{text[:50]}...\"" if len(text) > 50 else f'Text layer added: "{text}"',
                data={"text": text, "x": x, "y": y, "font": font_name, "size": font_size},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="add_text", error=str(e)).model_dump()

    @mcp.tool()
    def edit_clear() -> dict[str, Any]:
        """Clear the current selection area (make it transparent).

        WHEN TO USE: To erase part of a layer. The cleared area becomes
        transparent if the layer has an alpha channel.

        Requires: Active layer must have an alpha channel. Use
        add_alpha_channel first if needed.
        """
        code = _get_drawable_code() + [
            "Gimp.Drawable.edit_clear(drawable)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="edit_clear", message="Selection cleared"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="edit_clear", error=str(e)).model_dump()
