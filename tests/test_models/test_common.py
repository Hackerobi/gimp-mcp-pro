"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from gimp_mcp_pro.models.common import Color, OperationResult, Point, Region, BlendMode, SelectionOp
from gimp_mcp_pro.models.image import CreateImageParams, ExportImageParams
from gimp_mcp_pro.models.layer import CreateLayerParams
from gimp_mcp_pro.models.selection import SelectPolygonParams


class TestColor:
    def test_named_colors(self):
        for name in ["red", "blue", "white", "black", "transparent"]:
            c = Color(value=name)
            assert c.value == name

    def test_hex_colors(self):
        c = Color(value="#FF0000")
        assert c.value == "#FF0000"
        c = Color(value="#F00")
        assert c.value == "#F00"
        c = Color(value="#FF000080")
        assert c.value == "#FF000080"

    def test_rgb_colors(self):
        c = Color(value="rgb(255, 0, 0)")
        assert c.value == "rgb(255, 0, 0)"

    def test_rgba_colors(self):
        c = Color(value="rgba(255, 0, 0, 0.5)")
        assert c.value == "rgba(255, 0, 0, 0.5)"

    def test_invalid_color_raises(self):
        with pytest.raises(ValidationError):
            Color(value="notacolor")
        with pytest.raises(ValidationError):
            Color(value="#GGGGGG")
        with pytest.raises(ValidationError):
            Color(value="rgb(300, 0, 0)")

    def test_rgba_invalid_alpha(self):
        with pytest.raises(ValidationError):
            Color(value="rgba(255, 0, 0, 2.0)")

    def test_to_gegl_code(self):
        c = Color(value="red")
        assert c.to_gegl_code() == "Gegl.Color.new('red')"
        c = Color(value="#FF0000")
        assert c.to_gegl_code() == "Gegl.Color.new('#FF0000')"

    def test_case_insensitive_names(self):
        c = Color(value="RED")
        assert c.value == "red"
        c = Color(value="  Blue  ")
        assert c.value == "blue"


class TestOperationResult:
    def test_ok(self):
        r = OperationResult.ok("test_op", message="done", data={"x": 1})
        assert r.success is True
        assert r.operation == "test_op"
        assert r.message == "done"
        assert r.data == {"x": 1}
        assert r.error is None
        assert r.timestamp > 0

    def test_fail(self):
        r = OperationResult.fail("test_op", error="boom")
        assert r.success is False
        assert r.error == "boom"

    def test_model_dump(self):
        r = OperationResult.ok("test")
        d = r.model_dump()
        assert isinstance(d, dict)
        assert d["success"] is True
        assert d["operation"] == "test"


class TestRegion:
    def test_valid(self):
        r = Region(x=0, y=0, width=100, height=200)
        assert r.width == 100

    def test_invalid_zero_width(self):
        with pytest.raises(ValidationError):
            Region(x=0, y=0, width=0, height=100)

    def test_invalid_negative_x(self):
        with pytest.raises(ValidationError):
            Region(x=-1, y=0, width=100, height=100)


class TestCreateImageParams:
    def test_defaults(self):
        p = CreateImageParams(width=800, height=600)
        assert p.color_mode.value == "rgb"
        assert p.fill.value == "white"

    def test_max_dimensions(self):
        with pytest.raises(ValidationError):
            CreateImageParams(width=50000, height=600)


class TestCreateLayerParams:
    def test_defaults(self):
        p = CreateLayerParams()
        assert p.name == "New Layer"
        assert p.opacity == 100.0
        assert p.blend_mode == BlendMode.NORMAL
        assert p.has_alpha is True

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            CreateLayerParams(name="   ")


class TestSelectPolygonParams:
    def test_valid(self):
        p = SelectPolygonParams(points=[0, 0, 100, 0, 50, 100])
        assert len(p.points) == 6

    def test_too_few_points(self):
        with pytest.raises(ValidationError):
            SelectPolygonParams(points=[0, 0, 100, 0])

    def test_odd_count(self):
        with pytest.raises(ValidationError):
            SelectPolygonParams(points=[0, 0, 100, 0, 50])
