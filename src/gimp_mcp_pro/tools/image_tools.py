"""Image management tools for GIMP MCP Pro.

Covers creating, opening, saving, exporting, and managing images.
"""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge
from gimp_mcp_pro.models.common import FillType, OperationResult
from gimp_mcp_pro.models.image import CreateImageParams, ExportFormat, ExportImageParams, ImageInfo
from gimp_mcp_pro.utils.errors import GimpCommandError
from gimp_mcp_pro.utils.gimp_constants import FILL_TYPE_MAP, IMAGE_BASE_TYPE_MAP

logger = logging.getLogger("gimp_mcp_pro.tools.image")


def _get_active_image_code() -> list[str]:
    """Helper: Python code to get the active image and validate it exists."""
    return [
        "images = Gimp.get_images()",
        "if not images: raise RuntimeError('No images are open in GIMP')",
        "image = images[0]",
    ]


def register_image_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all image management tools with the MCP server."""

    @mcp.tool()
    def create_image(
        width: int,
        height: int,
        color_mode: str = "rgb",
        fill: str = "white",
    ) -> dict[str, Any]:
        """Create a new blank image in GIMP.

        WHEN TO USE: Starting a new project, creating a canvas for drawing.

        Args:
            width: Image width in pixels (1-32768)
            height: Image height in pixels (1-32768)
            color_mode: Color mode — "rgb", "grayscale", or "indexed"
            fill: Initial fill — "white", "transparent", "foreground", or "background"

        Returns:
            Operation result with image info in data field.
        """
        params = CreateImageParams(
            width=width,
            height=height,
            color_mode=color_mode,
            fill=fill,
        )

        base_type = IMAGE_BASE_TYPE_MAP.get(params.color_mode, "Gimp.ImageBaseType.RGB")
        fill_type = FILL_TYPE_MAP.get(params.fill, "Gimp.FillType.WHITE")

        # Determine image type for layer (with/without alpha)
        has_alpha = params.fill == FillType.TRANSPARENT
        if params.color_mode.value == "rgb":
            img_type = "Gimp.ImageType.RGBA_IMAGE" if has_alpha else "Gimp.ImageType.RGB_IMAGE"
        elif params.color_mode.value == "grayscale":
            img_type = "Gimp.ImageType.GRAYA_IMAGE" if has_alpha else "Gimp.ImageType.GRAY_IMAGE"
        else:
            img_type = "Gimp.ImageType.INDEXEDA_IMAGE" if has_alpha else "Gimp.ImageType.INDEXED_IMAGE"

        code = [
            "from gi.repository import Gimp, Gegl",
            f"image = Gimp.Image.new({params.width}, {params.height}, {base_type})",
            f"layer = Gimp.Layer.new(image, 'Background', {params.width}, {params.height}, "
            f"{img_type}, 100, Gimp.LayerMode.NORMAL)",
            "image.insert_layer(layer, None, 0)",
            f"Gimp.Drawable.edit_fill(layer, {fill_type})",
            "Gimp.Display.new(image)",
            "Gimp.displays_flush()",
            f"print(image.get_id() if hasattr(image, 'get_id') else 0)",
        ]

        try:
            result = bridge.execute_python(code)
            return OperationResult.ok(
                operation="create_image",
                message=f"Created {params.width}x{params.height} {params.color_mode.value} image",
                data={
                    "width": params.width,
                    "height": params.height,
                    "color_mode": params.color_mode.value,
                    "fill": params.fill.value,
                },
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="create_image",
                error=str(e),
            ).model_dump()

    @mcp.tool()
    def list_images() -> dict[str, Any]:
        """List all currently open images in GIMP.

        WHEN TO USE: Before operations that need to target a specific image,
        or to verify what images are available.

        Returns:
            Operation result with list of image info dicts.
        """
        code = [
            "import json",
            "images = Gimp.get_images()",
            "result = []",
            "for img in images:\n"
            "    info = {\n"
            "        'width': img.get_width(),\n"
            "        'height': img.get_height(),\n"
            "        'base_type': str(img.get_base_type()),\n"
            "        'num_layers': len(img.get_layers()),\n"
            "        'is_dirty': img.is_dirty() if hasattr(img, 'is_dirty') else False,\n"
            "    }\n"
            "    try:\n"
            "        f = img.get_file()\n"
            "        if f:\n"
            "            info['file_path'] = f.get_path() if hasattr(f, 'get_path') else None\n"
            "            info['file_name'] = f.get_basename() if hasattr(f, 'get_basename') else None\n"
            "    except: pass\n"
            "    result.append(info)",
            "print(json.dumps(result))",
        ]

        try:
            result = bridge.execute_python(code)
            outputs = result.get("results", [])
            # Parse the JSON output from the last print statement
            import json as _json

            images_data = []
            for out in outputs:
                if out and out.strip():
                    try:
                        images_data = _json.loads(out.strip())
                        break
                    except _json.JSONDecodeError:
                        continue

            return OperationResult.ok(
                operation="list_images",
                message=f"Found {len(images_data)} open image(s)",
                data={"images": images_data, "count": len(images_data)},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="list_images", error=str(e)
            ).model_dump()

    @mcp.tool()
    def get_image_info() -> dict[str, Any]:
        """Get detailed metadata about the active image (no bitmap data).

        WHEN TO USE: Before any operation, to understand the current canvas
        dimensions, layer structure, and file state. Much faster than
        get_image_bitmap since it doesn't export pixel data.

        COMBINES WITH: Use before create_layer (to match dimensions),
        before drawing (to verify layer structure), or before export
        (to check if image has unsaved changes).

        Returns:
            Comprehensive image metadata including layers, channels, file info.
        """
        try:
            result = bridge.get_image_metadata()
            if result.get("status") == "success":
                return OperationResult.ok(
                    operation="get_image_info",
                    message="Image metadata retrieved",
                    data=result.get("results", {}),
                ).model_dump()
            else:
                return OperationResult.fail(
                    operation="get_image_info",
                    error=result.get("error", "Failed to get image metadata"),
                ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="get_image_info", error=str(e)
            ).model_dump()

    @mcp.tool()
    def export_image(
        file_path: str,
        format: str | None = None,
        quality: int = 85,
    ) -> dict[str, Any]:
        """Export the active image to a file.

        WHEN TO USE: Saving the final result as PNG, JPEG, etc.

        Args:
            file_path: Output path (e.g., "/home/user/output.png")
            format: Export format — "png", "jpeg", "tiff", "bmp", "webp".
                    Auto-detected from file extension if not specified.
            quality: Quality for lossy formats like JPEG (1-100). Default 85.

        Returns:
            Operation result confirming export.
        """
        params = ExportImageParams(
            file_path=file_path,
            format=format,
            quality=quality,
        )

        # Build export code based on format
        ext = params.file_path.rsplit(".", 1)[-1].lower() if "." in params.file_path else "png"
        fmt = params.format.value if params.format else ext

        code = _get_active_image_code() + [
            "from gi.repository import Gio",
            f"file_obj = Gio.File.new_for_path('{params.file_path}')",
        ]

        if fmt == "png":
            code += [
                "export_proc = Gimp.get_pdb().lookup_procedure('file-png-export')",
                "if not export_proc: raise RuntimeError('PNG export procedure not found')",
                "config = export_proc.create_config()",
                "config.set_property('image', image)",
                "config.set_property('file', file_obj)",
                "try: config.set_property('drawables', image.get_layers())\nexcept: pass",
                "export_proc.run(config)",
            ]
        elif fmt in ("jpeg", "jpg"):
            code += [
                "export_proc = Gimp.get_pdb().lookup_procedure('file-jpeg-export')",
                "if not export_proc: raise RuntimeError('JPEG export procedure not found')",
                "config = export_proc.create_config()",
                "config.set_property('image', image)",
                "config.set_property('file', file_obj)",
                f"try: config.set_property('quality', {params.quality / 100.0})\nexcept: pass",
                "try: config.set_property('drawables', image.get_layers())\nexcept: pass",
                "export_proc.run(config)",
            ]
        else:
            # Generic fallback using Gimp.file_save
            code += [
                "Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, file_obj)",
            ]

        code.append(f"print('Exported to {params.file_path}')")

        try:
            bridge.execute_python(code, timeout=60.0)
            return OperationResult.ok(
                operation="export_image",
                message=f"Exported to {params.file_path}",
                data={"file_path": params.file_path, "format": fmt},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="export_image", error=str(e)
            ).model_dump()

    @mcp.tool()
    def flatten_image() -> dict[str, Any]:
        """Flatten all layers into a single layer.

        WHEN TO USE: Before final export when you want to merge all layers,
        or to simplify a complex layer structure.

        WARNING: This is destructive — you lose individual layer editability.
        Consider using undo groups so the user can revert.

        Returns:
            Operation result.
        """
        code = _get_active_image_code() + [
            "image.flatten()",
            "Gimp.displays_flush()",
            "print('Image flattened')",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="flatten_image",
                message="All layers flattened into one",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="flatten_image", error=str(e)
            ).model_dump()

    @mcp.tool()
    def duplicate_image() -> dict[str, Any]:
        """Duplicate the entire active image (all layers, channels, paths).

        WHEN TO USE: Creating a copy to experiment on without affecting
        the original. Good before destructive operations.

        Returns:
            Operation result with info about the new image.
        """
        code = _get_active_image_code() + [
            "new_image = image.duplicate()",
            "Gimp.Display.new(new_image)",
            "Gimp.displays_flush()",
            "print(f'{new_image.get_width()}x{new_image.get_height()}')",
        ]
        try:
            result = bridge.execute_python(code)
            return OperationResult.ok(
                operation="duplicate_image",
                message="Image duplicated",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="duplicate_image", error=str(e)
            ).model_dump()
