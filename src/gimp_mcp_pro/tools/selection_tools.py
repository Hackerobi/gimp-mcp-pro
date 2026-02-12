"""Selection tools for GIMP MCP Pro."""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge
from gimp_mcp_pro.models.common import OperationResult, SelectionOp
from gimp_mcp_pro.utils.errors import GimpCommandError
from gimp_mcp_pro.utils.gimp_constants import SELECTION_OP_MAP

logger = logging.getLogger("gimp_mcp_pro.tools.selection")


def _op_expr(op: str) -> str:
    """Convert selection op string to GIMP expression."""
    return SELECTION_OP_MAP.get(SelectionOp(op), "Gimp.ChannelOps.REPLACE")


def register_selection_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all selection tools with the MCP server."""

    @mcp.tool()
    def select_rectangle(
        x: float, y: float, width: float, height: float,
        operation: str = "replace",
        feather_radius: float = 0.0,
    ) -> dict[str, Any]:
        """Create a rectangular selection.

        WHEN TO USE: Before filling a rectangular area, or to constrain
        operations to a specific region.

        Args:
            x, y: Top-left corner
            width, height: Selection dimensions
            operation: "replace", "add", "subtract", or "intersect"
            feather_radius: Edge feather radius (0 = sharp edges, recommended default)
        """
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            f"Gimp.Image.select_rectangle(image, {_op_expr(operation)}, {x}, {y}, {width}, {height})",
        ]
        if feather_radius > 0:
            code.append(f"Gimp.Selection.feather(image, {feather_radius})")
        code.append("Gimp.displays_flush()")

        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="select_rectangle",
                message=f"Selected rectangle ({x},{y}) {width}x{height}",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_rectangle", error=str(e)).model_dump()

    @mcp.tool()
    def select_ellipse(
        x: float, y: float, width: float, height: float,
        operation: str = "replace",
        feather_radius: float = 0.0,
    ) -> dict[str, Any]:
        """Create an elliptical selection.

        For a circular selection, set width == height.

        Args:
            x, y: Bounding box top-left corner
            width, height: Bounding box dimensions
            operation: "replace", "add", "subtract", or "intersect"
            feather_radius: Edge feather radius (0 = sharp, recommended)
        """
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            f"Gimp.Image.select_ellipse(image, {_op_expr(operation)}, {x}, {y}, {width}, {height})",
        ]
        if feather_radius > 0:
            code.append(f"Gimp.Selection.feather(image, {feather_radius})")
        code.append("Gimp.displays_flush()")

        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="select_ellipse",
                message=f"Selected ellipse at ({x},{y}) {width}x{height}",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_ellipse", error=str(e)).model_dump()

    @mcp.tool()
    def select_polygon(
        points: list[float],
        operation: str = "replace",
        feather_radius: float = 0.0,
    ) -> dict[str, Any]:
        """Create a polygon (freeform) selection.

        BEST PRACTICE: Use polygon selection + fill_selection for solid shapes.
        This is the recommended way to draw filled shapes in GIMP.

        Args:
            points: Flat list [x1,y1, x2,y2, x3,y3, ...]. Min 3 vertices (6 values).
            operation: "replace", "add", "subtract", or "intersect"
            feather_radius: Edge feather radius (0 = sharp, recommended)
        """
        if len(points) < 6 or len(points) % 2 != 0:
            return OperationResult.fail(
                operation="select_polygon",
                error="Need at least 3 points (6 values) with even count",
            ).model_dump()

        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            f"Gimp.Image.select_polygon(image, {_op_expr(operation)}, {points})",
        ]
        if feather_radius > 0:
            code.append(f"Gimp.Selection.feather(image, {feather_radius})")
        code.append("Gimp.displays_flush()")

        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="select_polygon",
                message=f"Selected polygon with {len(points)//2} vertices",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_polygon", error=str(e)).model_dump()

    @mcp.tool()
    def select_all() -> dict[str, Any]:
        """Select the entire image."""
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "Gimp.Selection.all(images[0])",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(operation="select_all", message="Selected all").model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_all", error=str(e)).model_dump()

    @mcp.tool()
    def select_none() -> dict[str, Any]:
        """Clear all selections.

        IMPORTANT: Always call this after fill/stroke operations on selections
        to avoid unexpected behavior on subsequent operations.
        """
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "Gimp.Selection.none(images[0])",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(operation="select_none", message="Selection cleared").model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_none", error=str(e)).model_dump()

    @mcp.tool()
    def select_invert() -> dict[str, Any]:
        """Invert the current selection (select everything NOT currently selected)."""
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "Gimp.Selection.invert(images[0])",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(operation="select_invert", message="Selection inverted").model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_invert", error=str(e)).model_dump()

    @mcp.tool()
    def select_grow(radius: int) -> dict[str, Any]:
        """Grow the current selection by a number of pixels.

        Args:
            radius: Number of pixels to grow the selection by.
        """
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            f"Gimp.Selection.grow(images[0], {radius})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="select_grow", message=f"Selection grown by {radius}px"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_grow", error=str(e)).model_dump()

    @mcp.tool()
    def select_shrink(radius: int) -> dict[str, Any]:
        """Shrink the current selection by a number of pixels.

        Args:
            radius: Number of pixels to shrink the selection by.
        """
        code = [
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            f"Gimp.Selection.shrink(images[0], {radius})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="select_shrink", message=f"Selection shrunk by {radius}px"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="select_shrink", error=str(e)).model_dump()
