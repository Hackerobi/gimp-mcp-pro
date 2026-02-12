"""Tests for Phase 2 tools — transform, filter, color validation."""

import pytest
from pydantic import ValidationError

from gimp_mcp_pro.models.common import Color, BlendMode, FillType, SelectionOp, InterpolationType


class TestColorExtended:
    def test_rgb_max_values(self):
        c = Color(value="rgb(255, 255, 255)")
        assert "255" in c.value

    def test_rgba_zero_alpha(self):
        c = Color(value="rgba(255, 0, 0, 0.0)")
        assert c.value == "rgba(255, 0, 0, 0.0)"

    def test_hex_8_digit(self):
        c = Color(value="#FF000080")
        assert c.value == "#FF000080"

    def test_transparent_named(self):
        c = Color(value="transparent")
        assert c.value == "transparent"

    def test_gegl_code_rgb(self):
        c = Color(value="rgb(100, 200, 50)")
        assert "Gegl.Color.new" in c.to_gegl_code()


class TestEnums:
    def test_blend_modes_complete(self):
        assert len(BlendMode) >= 20
        assert BlendMode.NORMAL.value == "normal"
        assert BlendMode.MULTIPLY.value == "multiply"
        assert BlendMode.OVERLAY.value == "overlay"

    def test_fill_types_complete(self):
        assert FillType.FOREGROUND.value == "foreground"
        assert FillType.TRANSPARENT.value == "transparent"

    def test_selection_ops_complete(self):
        for name in ["replace", "add", "subtract", "intersect"]:
            assert SelectionOp(name)

    def test_interpolation_types(self):
        for name in ["none", "linear", "cubic", "nohalo", "lohalo"]:
            assert InterpolationType(name)


class TestGimpConstantMaps:
    def test_all_selection_ops_mapped(self):
        from gimp_mcp_pro.utils.gimp_constants import SELECTION_OP_MAP
        for op in SelectionOp:
            assert op in SELECTION_OP_MAP

    def test_all_fill_types_mapped(self):
        from gimp_mcp_pro.utils.gimp_constants import FILL_TYPE_MAP
        for ft in FillType:
            assert ft in FILL_TYPE_MAP

    def test_all_blend_modes_mapped(self):
        from gimp_mcp_pro.utils.gimp_constants import BLEND_MODE_MAP
        for bm in BlendMode:
            assert bm in BLEND_MODE_MAP

    def test_all_interpolations_mapped(self):
        from gimp_mcp_pro.utils.gimp_constants import INTERPOLATION_MAP
        for it in InterpolationType:
            assert it in INTERPOLATION_MAP


class TestDrawingModels:
    def test_brush_stroke_valid(self):
        from gimp_mcp_pro.models.drawing import BrushStrokeParams
        p = BrushStrokeParams(points=[0, 0, 100, 100], tool="pencil")
        assert p.tool == "pencil"

    def test_brush_stroke_paintbrush(self):
        from gimp_mcp_pro.models.drawing import BrushStrokeParams
        p = BrushStrokeParams(points=[0, 0, 50, 50], tool="paintbrush")
        assert p.tool == "paintbrush"

    def test_brush_stroke_invalid_tool(self):
        from gimp_mcp_pro.models.drawing import BrushStrokeParams
        with pytest.raises(ValidationError):
            BrushStrokeParams(points=[0, 0, 50, 50], tool="airbrush")

    def test_brush_stroke_too_few_points(self):
        from gimp_mcp_pro.models.drawing import BrushStrokeParams
        with pytest.raises(ValidationError):
            BrushStrokeParams(points=[0, 0])

    def test_draw_shape_valid(self):
        from gimp_mcp_pro.models.drawing import DrawShapeParams
        p = DrawShapeParams(shape="rectangle", x=0, y=0, width=100, height=50)
        assert p.shape == "rectangle"
        assert p.filled is True

    def test_draw_shape_ellipse(self):
        from gimp_mcp_pro.models.drawing import DrawShapeParams
        p = DrawShapeParams(shape="ellipse", x=10, y=10, width=50, height=50, filled=False)
        assert p.filled is False

    def test_draw_shape_invalid(self):
        from gimp_mcp_pro.models.drawing import DrawShapeParams
        with pytest.raises(ValidationError):
            DrawShapeParams(shape="triangle", x=0, y=0, width=100, height=100)

    def test_fill_params_defaults(self):
        from gimp_mcp_pro.models.drawing import FillParams
        p = FillParams()
        assert p.fill_type == FillType.FOREGROUND
        assert p.color is None

    def test_bucket_fill_params(self):
        from gimp_mcp_pro.models.drawing import BucketFillParams
        p = BucketFillParams(x=50, y=50, threshold=20.0)
        assert p.threshold == 20.0
        assert p.sample_merged is False


class TestSelectionModels:
    def test_select_by_color(self):
        from gimp_mcp_pro.models.selection import SelectByColorParams
        p = SelectByColorParams(x=100, y=100, threshold=30.0)
        assert p.operation == SelectionOp.REPLACE
        assert p.sample_merged is False

    def test_select_rectangle_with_feather(self):
        from gimp_mcp_pro.models.selection import SelectRectangleParams
        p = SelectRectangleParams(x=0, y=0, width=200, height=100, feather=True, feather_radius=5.0)
        assert p.feather is True
        assert p.feather_radius == 5.0


class TestImageModels:
    def test_export_png(self):
        from gimp_mcp_pro.models.image import ExportImageParams, ExportFormat
        p = ExportImageParams(file_path="/tmp/test.png")
        assert p.quality == 85
        assert p.compression == 9

    def test_export_jpeg_quality(self):
        from gimp_mcp_pro.models.image import ExportImageParams, ExportFormat
        p = ExportImageParams(file_path="/tmp/test.jpg", format=ExportFormat.JPEG, quality=95)
        assert p.quality == 95

    def test_export_empty_path_fails(self):
        from gimp_mcp_pro.models.image import ExportImageParams
        with pytest.raises(ValidationError):
            ExportImageParams(file_path="   ")

    def test_image_info_defaults(self):
        from gimp_mcp_pro.models.image import ImageInfo
        info = ImageInfo(
            image_id=1, width=800, height=600,
            color_mode="RGB", num_layers=2,
        )
        assert info.is_dirty is False
        assert info.layers == []


class TestLayerModels:
    def test_layer_info(self):
        from gimp_mcp_pro.models.layer import LayerInfo
        info = LayerInfo(
            layer_id=1, name="Test", width=100, height=100,
            opacity=75.0, blend_mode="normal", visible=True,
            has_alpha=True,
        )
        assert info.is_group is False
        assert info.children == []

    def test_set_layer_property(self):
        from gimp_mcp_pro.models.layer import SetLayerPropertyParams
        p = SetLayerPropertyParams(opacity=50.0)
        assert p.opacity == 50.0
        assert p.blend_mode is None

    def test_set_layer_property_by_name(self):
        from gimp_mcp_pro.models.layer import SetLayerPropertyParams
        p = SetLayerPropertyParams(layer_name="Background", visible=False)
        assert p.layer_name == "Background"
        assert p.visible is False


class TestPromptFiles:
    """Verify prompt markdown files exist and have content."""

    def test_best_practices_exists(self):
        from pathlib import Path
        path = Path(__file__).parent.parent / "src" / "gimp_mcp_pro" / "prompts" / "best_practices.md"
        assert path.exists(), f"Missing: {path}"
        content = path.read_text()
        assert len(content) > 100
        assert "selection" in content.lower()

    def test_iterative_workflow_exists(self):
        from pathlib import Path
        path = Path(__file__).parent.parent / "src" / "gimp_mcp_pro" / "prompts" / "iterative_workflow.md"
        assert path.exists()
        content = path.read_text()
        assert "golden rule" in content.lower()

    def test_filter_catalog_exists(self):
        from pathlib import Path
        path = Path(__file__).parent.parent / "src" / "gimp_mcp_pro" / "prompts" / "filter_catalog.md"
        assert path.exists()
        content = path.read_text()
        assert "gaussian" in content.lower()

    def test_api_reference_exists(self):
        from pathlib import Path
        path = Path(__file__).parent.parent / "src" / "gimp_mcp_pro" / "prompts" / "api_reference.md"
        assert path.exists()
        content = path.read_text()
        assert "Gegl.Color" in content


class TestErrorTypes:
    def test_gimp_command_error(self):
        from gimp_mcp_pro.utils.errors import GimpCommandError
        e = GimpCommandError("test error", command="create_image", traceback="line 1")
        assert str(e) == "test error"
        assert e.command == "create_image"
        assert e.gimp_traceback == "line 1"

    def test_gimp_timeout_error(self):
        from gimp_mcp_pro.utils.errors import GimpTimeoutError
        e = GimpTimeoutError("timed out", timeout_seconds=30.0)
        assert e.timeout_seconds == 30.0

    def test_gimp_connection_error(self):
        from gimp_mcp_pro.utils.errors import GimpConnectionError
        e = GimpConnectionError("cannot connect")
        assert "connect" in str(e)
