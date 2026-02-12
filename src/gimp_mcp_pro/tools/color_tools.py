"""Color adjustment tools for GIMP MCP Pro.

Covers brightness/contrast, levels, curves, hue-saturation, desaturation,
color inversion, threshold, posterize, and color-to-alpha.
"""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge, LONG_TIMEOUT
from gimp_mcp_pro.models.common import Color, OperationResult
from gimp_mcp_pro.utils.errors import GimpCommandError

logger = logging.getLogger("gimp_mcp_pro.tools.color")


def _color_preamble(layer_name: str | None, layer_index: int | None) -> list[str]:
    """Standard preamble for color adjustment tools."""
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


def register_color_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register all color adjustment tools with the MCP server."""

    @mcp.tool()
    def adjust_brightness_contrast(
        brightness: int = 0,
        contrast: int = 0,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Adjust brightness and contrast of a layer.

        Args:
            brightness: Brightness adjustment (-127 to 127, 0 = no change)
            contrast: Contrast adjustment (-127 to 127, 0 = no change)
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        brightness = max(-127, min(127, brightness))
        contrast = max(-127, min(127, contrast))

        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.brightness_contrast(drawable, {brightness / 127.0}, {contrast / 127.0})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="adjust_brightness_contrast",
                message=f"Brightness={brightness}, Contrast={contrast}",
                data={"brightness": brightness, "contrast": contrast},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="adjust_brightness_contrast", error=str(e)
            ).model_dump()

    @mcp.tool()
    def adjust_hue_saturation(
        hue: float = 0.0,
        saturation: float = 0.0,
        lightness: float = 0.0,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Adjust hue, saturation, and lightness of a layer.

        Args:
            hue: Hue rotation in degrees (-180 to 180, 0 = no change)
            saturation: Saturation adjustment (-100 to 100, 0 = no change)
            lightness: Lightness adjustment (-100 to 100, 0 = no change)
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        hue = max(-180.0, min(180.0, hue))
        saturation = max(-100.0, min(100.0, saturation))
        lightness = max(-100.0, min(100.0, lightness))

        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.hue_saturation(drawable, Gimp.HueRange.ALL, "
            f"{hue}, {lightness}, {saturation}, 0.0)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="adjust_hue_saturation",
                message=f"Hue={hue}°, Saturation={saturation}, Lightness={lightness}",
                data={"hue": hue, "saturation": saturation, "lightness": lightness},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="adjust_hue_saturation", error=str(e)
            ).model_dump()

    @mcp.tool()
    def adjust_levels(
        input_low: int = 0,
        input_high: int = 255,
        gamma: float = 1.0,
        output_low: int = 0,
        output_high: int = 255,
        channel: str = "value",
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Adjust levels for a layer.

        WHEN TO USE: Fine-tuning tonal range, fixing underexposed/overexposed
        images, adjusting individual color channels.

        Args:
            input_low: Input black point (0-255)
            input_high: Input white point (0-255)
            gamma: Midtone gamma (0.1-10.0, 1.0 = no change)
            output_low: Output black point (0-255)
            output_high: Output white point (0-255)
            channel: "value" (all), "red", "green", "blue", "alpha"
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        channel_map = {
            "value": "Gimp.HistogramChannel.VALUE",
            "red": "Gimp.HistogramChannel.RED",
            "green": "Gimp.HistogramChannel.GREEN",
            "blue": "Gimp.HistogramChannel.BLUE",
            "alpha": "Gimp.HistogramChannel.ALPHA",
        }
        ch_expr = channel_map.get(channel.lower(), "Gimp.HistogramChannel.VALUE")

        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.levels(drawable, {ch_expr}, "
            f"{input_low / 255.0}, {input_high / 255.0}, False, "
            f"{gamma}, "
            f"{output_low / 255.0}, {output_high / 255.0}, False)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="adjust_levels",
                message=f"Levels adjusted ({channel}): input [{input_low}-{input_high}], gamma {gamma}",
                data={"channel": channel, "input_low": input_low, "input_high": input_high,
                      "gamma": gamma, "output_low": output_low, "output_high": output_high},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="adjust_levels", error=str(e)).model_dump()

    @mcp.tool()
    def adjust_curves(
        control_points: list[float],
        channel: str = "value",
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Adjust curves for a layer.

        WHEN TO USE: Fine-grained tonal control, creating custom contrast curves,
        cross-processing effects.

        Args:
            control_points: Flat list of input/output pairs [in1,out1, in2,out2, ...].
                           Values are 0.0-1.0 (0=black, 1=white).
                           Example: [0,0, 0.25,0.2, 0.5,0.6, 0.75,0.85, 1,1] for S-curve.
            channel: "value", "red", "green", "blue", "alpha"
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        if len(control_points) < 4 or len(control_points) % 2 != 0:
            return OperationResult.fail(
                operation="adjust_curves",
                error="control_points must have at least 2 pairs (4 values) with even count",
            ).model_dump()

        channel_map = {
            "value": "Gimp.HistogramChannel.VALUE",
            "red": "Gimp.HistogramChannel.RED",
            "green": "Gimp.HistogramChannel.GREEN",
            "blue": "Gimp.HistogramChannel.BLUE",
            "alpha": "Gimp.HistogramChannel.ALPHA",
        }
        ch_expr = channel_map.get(channel.lower(), "Gimp.HistogramChannel.VALUE")

        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.curves_spline(drawable, {ch_expr}, {control_points})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            n_points = len(control_points) // 2
            return OperationResult.ok(
                operation="adjust_curves",
                message=f"Curves adjusted ({channel}, {n_points} control points)",
                data={"channel": channel, "num_points": n_points},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="adjust_curves", error=str(e)).model_dump()

    @mcp.tool()
    def desaturate(
        method: str = "luminosity",
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Convert a layer to grayscale while keeping it in RGB mode.

        Args:
            method: Desaturation method —
                    "luminosity" (perceptual, recommended),
                    "average" (equal weight),
                    "lightness" (HSL lightness),
                    "luminance" (linear luminance)
            layer_name: Target layer. Uses active layer if not specified.
            layer_index: Target layer by index.
        """
        method_map = {
            "luminosity": "Gimp.DesaturateMode.LUMA",
            "luma": "Gimp.DesaturateMode.LUMA",
            "average": "Gimp.DesaturateMode.AVERAGE",
            "lightness": "Gimp.DesaturateMode.LIGHTNESS",
            "luminance": "Gimp.DesaturateMode.LUMINANCE",
            "value": "Gimp.DesaturateMode.VALUE",
        }
        m_expr = method_map.get(method.lower().strip(), "Gimp.DesaturateMode.LUMA")

        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.desaturate(drawable, {m_expr})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="desaturate",
                message=f"Desaturated using {method} method",
                data={"method": method},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="desaturate", error=str(e)).model_dump()

    @mcp.tool()
    def invert_colors(
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Invert all colors in a layer (negative effect).

        Each pixel's color is replaced with its complement.
        """
        code = _color_preamble(layer_name, layer_index) + [
            "Gimp.Drawable.invert(drawable, False)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="invert_colors", message="Colors inverted"
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="invert_colors", error=str(e)).model_dump()

    @mcp.tool()
    def apply_threshold(
        low: int = 128,
        high: int = 255,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Apply threshold — convert to pure black and white.

        Pixels darker than `low` become black, lighter than `high` become white.

        Args:
            low: Lower threshold (0-255, default 128)
            high: Upper threshold (0-255, default 255)
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.threshold(drawable, Gimp.HistogramChannel.VALUE, "
            f"{low / 255.0}, {high / 255.0})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="apply_threshold",
                message=f"Threshold applied ({low}-{high})",
                data={"low": low, "high": high},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="apply_threshold", error=str(e)).model_dump()

    @mcp.tool()
    def posterize(
        levels: int = 4,
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Reduce the number of color levels (posterization effect).

        Args:
            levels: Number of color levels per channel (2-256, lower = more dramatic)
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        levels = max(2, min(256, levels))

        code = _color_preamble(layer_name, layer_index) + [
            f"Gimp.Drawable.posterize(drawable, {levels})",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="posterize",
                message=f"Posterized to {levels} levels",
                data={"levels": levels},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="posterize", error=str(e)).model_dump()

    @mcp.tool()
    def color_to_alpha(
        color: str = "white",
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Make a specific color transparent (color to alpha).

        WHEN TO USE: Removing backgrounds, making white/black transparent
        for compositing, creating cutouts.

        Args:
            color: Color to make transparent — name, hex, or rgb.
            layer_name: Target layer.
            layer_index: Target layer by index.
        """
        c = Color(value=color)

        code = _color_preamble(layer_name, layer_index) + [
            "if not drawable.has_alpha(): drawable.add_alpha()",
            f"gegl_color = {c.to_gegl_code()}",
            "df = Gimp.DrawableFilter.new(drawable, 'gegl:color-to-alpha', '')",
            "cfg = df.get_config()",
            "cfg.set_property('color', gegl_color)",
            "drawable.append_filter(df)",
            "drawable.merge_filter(df)",
            "Gimp.displays_flush()",
        ]

        try:
            bridge.execute_python(code, timeout=LONG_TIMEOUT)
            return OperationResult.ok(
                operation="color_to_alpha",
                message=f"Color '{color}' made transparent",
                data={"color": color},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="color_to_alpha", error=str(e)).model_dump()

    @mcp.tool()
    def auto_white_balance(
        layer_name: str | None = None,
        layer_index: int | None = None,
    ) -> dict[str, Any]:
        """Automatically adjust white balance (stretch colors).

        Performs automatic levels adjustment to normalize color distribution.
        """
        code = _color_preamble(layer_name, layer_index) + [
            "Gimp.Drawable.levels_stretch(drawable)",
            "Gimp.displays_flush()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="auto_white_balance",
                message="Auto white balance applied",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="auto_white_balance", error=str(e)).model_dump()

    @mcp.tool()
    def get_colors() -> dict[str, Any]:
        """Get the current foreground and background colors.

        WHEN TO USE: Before drawing to verify colors are set correctly,
        especially since the user can change them in GIMP's UI at any time.
        """
        code = [
            "import json",
            "from gi.repository import Gimp, Gegl",
            "fg = Gimp.context_get_foreground()",
            "bg = Gimp.context_get_background()",
            "result = {}",
            "def color_to_dict(c):\n"
            "    try:\n"
            "        rgba = c.get_rgba()\n"
            "        return {'r': round(rgba.red, 4), 'g': round(rgba.green, 4), 'b': round(rgba.blue, 4), 'a': round(rgba.alpha, 4)}\n"
            "    except:\n"
            "        return str(c)",
            "result['foreground'] = color_to_dict(fg)",
            "result['background'] = color_to_dict(bg)",
            "print(json.dumps(result))",
        ]
        try:
            result = bridge.execute_python(code)
            import json as _json
            colors_data = {}
            for out in result.get("results", []):
                if out and out.strip():
                    try:
                        colors_data = _json.loads(out.strip())
                        break
                    except _json.JSONDecodeError:
                        continue
            return OperationResult.ok(
                operation="get_colors",
                message="Current colors retrieved",
                data=colors_data,
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="get_colors", error=str(e)).model_dump()

    @mcp.tool()
    def swap_colors() -> dict[str, Any]:
        """Swap foreground and background colors."""
        code = [
            "from gi.repository import Gimp",
            "Gimp.context_swap_colors()",
        ]
        try:
            bridge.execute_python(code)
            return OperationResult.ok(
                operation="swap_colors",
                message="Foreground and background colors swapped",
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="swap_colors", error=str(e)).model_dump()

    @mcp.tool()
    def sample_color(
        x: int,
        y: int,
        sample_merged: bool = False,
    ) -> dict[str, Any]:
        """Pick/sample a color from a pixel in the image.

        Args:
            x: X coordinate to sample
            y: Y coordinate to sample
            sample_merged: If True, sample from all visible layers merged.
                          If False, sample from active layer only.
        """
        code = [
            "import json",
            "from gi.repository import Gimp, Gegl",
            "images = Gimp.get_images()",
            "if not images: raise RuntimeError('No images are open')",
            "image = images[0]",
            "sel = image.get_selected_layers()",
            "if not sel: raise RuntimeError('No active layer')",
            "drawable = sel[0]",
            "result = {}",
            "try:\n"
            f"    color = drawable.get_pixel({x}, {y})\n"
            "    rgba = color.get_rgba()\n"
            "    result = {'r': round(rgba.red, 4), 'g': round(rgba.green, 4), 'b': round(rgba.blue, 4), 'a': round(rgba.alpha, 4)}\n"
            "except Exception as e:\n"
            "    result = {'error': str(e)}",
            "print(json.dumps(result))",
        ]
        try:
            result = bridge.execute_python(code)
            import json as _json
            color_data = {}
            for out in result.get("results", []):
                if out and out.strip():
                    try:
                        color_data = _json.loads(out.strip())
                        break
                    except _json.JSONDecodeError:
                        continue
            return OperationResult.ok(
                operation="sample_color",
                message=f"Color sampled at ({x}, {y})",
                data=color_data,
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="sample_color", error=str(e)).model_dump()
