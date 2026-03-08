"""Tests for drawing core functions (_draw_*) and MCP tool wrappers."""

import pytest
from fastmcp.utilities.types import Image

from svg_mcp.canvas import Canvas, get_canvas, set_canvas
from svg_mcp.tools.drawing import (
    _draw_circle,
    _draw_ellipse,
    _draw_group,
    _draw_image,
    _draw_line,
    _draw_path,
    _draw_polygon,
    _draw_polyline,
    _draw_raw_svg,
    _draw_rect,
    _draw_text,
    draw_circle,
    draw_ellipse,
    draw_group,
    draw_image,
    draw_line,
    draw_path,
    draw_polygon,
    draw_polyline,
    draw_raw_svg,
    draw_rect,
    draw_text,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def svg() -> str:
    return get_canvas().to_svg()


def elements():
    return get_canvas().elements


# ---------------------------------------------------------------------------
# _draw_rect
# ---------------------------------------------------------------------------


class TestDrawRect:
    def test_auto_id(self):
        eid = _draw_rect(x=0, y=0, width=10, height=10)
        assert eid.startswith("el-")

    def test_explicit_id(self):
        eid = _draw_rect(x=0, y=0, width=10, height=10, element_id="r1")
        assert eid == "r1"

    def test_svg_content(self):
        _draw_rect(
            x=5,
            y=10,
            width=80,
            height=40,
            fill="red",
            stroke="blue",
            stroke_width=2,
            element_id="r",
        )
        s = svg()
        assert 'x="5"' in s
        assert 'y="10"' in s
        assert 'width="80"' in s
        assert 'height="40"' in s
        assert 'fill="red"' in s
        assert 'stroke="blue"' in s

    def test_rx_ry(self):
        _draw_rect(x=0, y=0, width=10, height=10, rx=3, ry=4, element_id="r")
        assert 'rx="3"' in svg()
        assert 'ry="4"' in svg()

    def test_rotation(self):
        _draw_rect(x=0, y=0, width=10, height=10, rotation=45, element_id="r")
        assert "rotate(45" in svg()

    def test_no_rotation_by_default(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        assert "rotate" not in svg()

    def test_stroke_dasharray(self):
        _draw_rect(
            x=0, y=0, width=10, height=10, stroke_dasharray="5,3", element_id="r"
        )
        assert 'stroke-dasharray="5,3"' in svg()

    def test_opacity(self):
        _draw_rect(x=0, y=0, width=10, height=10, opacity=0.5, element_id="r")
        assert 'opacity="0.5"' in svg()


# ---------------------------------------------------------------------------
# _draw_circle
# ---------------------------------------------------------------------------


class TestDrawCircle:
    def test_svg_content(self):
        _draw_circle(cx=50, cy=60, r=20, fill="green", element_id="c")
        s = svg()
        assert "<circle" in s
        assert 'cx="50"' in s
        assert 'cy="60"' in s
        assert 'r="20"' in s
        assert 'fill="green"' in s

    def test_dasharray(self):
        _draw_circle(cx=0, cy=0, r=5, stroke_dasharray="2,2", element_id="c")
        assert 'stroke-dasharray="2,2"' in svg()


# ---------------------------------------------------------------------------
# _draw_ellipse
# ---------------------------------------------------------------------------


class TestDrawEllipse:
    def test_svg_content(self):
        _draw_ellipse(cx=100, cy=100, rx=50, ry=30, element_id="e")
        s = svg()
        assert "<ellipse" in s
        assert 'rx="50"' in s
        assert 'ry="30"' in s

    def test_rotation(self):
        _draw_ellipse(cx=10, cy=10, rx=5, ry=3, rotation=30, element_id="e")
        assert "rotate(30" in svg()


# ---------------------------------------------------------------------------
# _draw_line
# ---------------------------------------------------------------------------


class TestDrawLine:
    def test_svg_content(self):
        _draw_line(x1=0, y1=0, x2=100, y2=100, stroke="red", element_id="l")
        s = svg()
        # drawsvg.Line produces a <path d="M{x1},{y1} L{x2},{y2}"> element
        assert "<path" in s or "<line" in s
        assert "0,0" in s or '"0"' in s
        assert 'stroke="red"' in s

    def test_linecap(self):
        _draw_line(x1=0, y1=0, x2=10, y2=10, stroke_linecap="square", element_id="l")
        assert 'stroke-linecap="square"' in svg()

    def test_default_linecap_round(self):
        _draw_line(x1=0, y1=0, x2=10, y2=10, element_id="l")
        assert 'stroke-linecap="round"' in svg()


# ---------------------------------------------------------------------------
# _draw_polyline
# ---------------------------------------------------------------------------


class TestDrawPolyline:
    def test_svg_content(self):
        _draw_polyline(points="0,0 50,50 100,0", element_id="pl")
        s = svg()
        # drawsvg.Lines(close=False) produces a <path d="M... L... L..."> fragment
        assert "<path" in s
        assert "0,0" in s or "M0" in s


# ---------------------------------------------------------------------------
# _draw_polygon
# ---------------------------------------------------------------------------


class TestDrawPolygon:
    def test_svg_content(self):
        _draw_polygon(points="100,10 40,198 190,78", fill="yellow", element_id="pg")
        s = svg()
        # drawsvg.Lines(close=True) produces a <path d="M... L... L... Z"> fragment
        assert "<path" in s
        assert 'fill="yellow"' in s


# ---------------------------------------------------------------------------
# _draw_path
# ---------------------------------------------------------------------------


class TestDrawPath:
    def test_svg_content(self):
        _draw_path(d="M10 80 L90 80", stroke="purple", element_id="p")
        s = svg()
        assert "<path" in s
        assert 'd="M10 80 L90 80"' in s
        assert 'stroke="purple"' in s


# ---------------------------------------------------------------------------
# _draw_text
# ---------------------------------------------------------------------------


class TestDrawText:
    def test_svg_content(self):
        _draw_text(x=10, y=20, text="Hello", font_size=24, fill="navy", element_id="t")
        s = svg()
        assert "<text" in s
        assert 'x="10"' in s
        assert 'y="20"' in s
        assert "Hello" in s
        assert 'font-size="24"' in s
        assert 'fill="navy"' in s

    def test_html_escaping(self):
        _draw_text(x=0, y=0, text='<>&"', element_id="t")
        s = svg()
        assert "&lt;" in s
        assert "&gt;" in s
        assert "&amp;" in s

    def test_text_anchor(self):
        _draw_text(x=0, y=0, text="X", text_anchor="middle", element_id="t")
        assert 'text-anchor="middle"' in svg()

    def test_font_weight(self):
        _draw_text(x=0, y=0, text="X", font_weight="bold", element_id="t")
        assert 'font-weight="bold"' in svg()

    def test_rotation(self):
        _draw_text(x=50, y=50, text="R", rotation=45, element_id="t")
        assert "rotate(45" in svg()


# ---------------------------------------------------------------------------
# _draw_image
# ---------------------------------------------------------------------------


class TestDrawImage:
    def test_svg_content(self):
        _draw_image(
            x=5,
            y=5,
            width=100,
            height=80,
            href="https://example.com/img.png",
            element_id="img",
        )
        s = svg()
        assert "<image" in s
        # drawsvg.Image uses xlink:href attribute
        assert "https://example.com/img.png" in s
        assert 'width="100"' in s
        assert 'height="80"' in s

    def test_opacity(self):
        _draw_image(
            x=0,
            y=0,
            width=10,
            height=10,
            href="data:image/png;base64,",
            opacity=0.3,
            element_id="img",
        )
        assert 'opacity="0.3"' in svg()


# ---------------------------------------------------------------------------
# _draw_group
# ---------------------------------------------------------------------------


class TestDrawGroup:
    def test_wraps_children(self):
        _draw_group(children='<circle cx="5" cy="5" r="3"/>', element_id="g")
        s = svg()
        assert "<g>" in s
        assert "<circle" in s

    def test_with_transform(self):
        _draw_group(children="<rect/>", transform="translate(10,20)", element_id="g")
        assert 'transform="translate(10,20)"' in svg()

    def test_with_opacity(self):
        _draw_group(children="<rect/>", opacity=0.5, element_id="g")
        assert 'opacity="0.5"' in svg()

    def test_no_extra_attrs_when_defaults(self):
        _draw_group(children="<rect/>", element_id="g")
        s = get_canvas().get_element_svg("g")
        assert s == "<g><rect/></g>"


# ---------------------------------------------------------------------------
# _draw_raw_svg
# ---------------------------------------------------------------------------


class TestDrawRawSvg:
    def test_stores_fragment_verbatim(self):
        frag = '<use href="#symbol1" x="10" y="20"/>'
        eid = _draw_raw_svg(frag, element_id="u")
        assert get_canvas().get_element_svg("u") == frag


# ---------------------------------------------------------------------------
# MCP tool wrappers — return types and schema compatibility
# ---------------------------------------------------------------------------


class TestMcpToolWrappers:
    """MCP wrappers must return list[ContentBlock] with no anyOf in schemas."""

    def _check_result(self, result):
        assert isinstance(result, list)
        assert len(result) >= 1
        # Last item is always the PNG preview
        img = result[-1]
        assert isinstance(img, Image)
        assert img._mime_type == "image/png"

    def test_draw_rect_result(self):
        self._check_result(draw_rect(x=0, y=0, width=10, height=10))

    def test_draw_circle_result(self):
        self._check_result(draw_circle(cx=5, cy=5, r=3))

    def test_draw_ellipse_result(self):
        self._check_result(draw_ellipse(cx=5, cy=5, rx=4, ry=2))

    def test_draw_line_result(self):
        self._check_result(draw_line(x1=0, y1=0, x2=10, y2=10))

    def test_draw_polyline_result(self):
        self._check_result(draw_polyline(points="0,0 10,10"))

    def test_draw_polygon_result(self):
        self._check_result(draw_polygon(points="0,0 10,0 5,10"))

    def test_draw_path_result(self):
        self._check_result(draw_path(d="M0 0 L10 10"))

    def test_draw_text_result(self):
        self._check_result(draw_text(x=0, y=10, text="Hi"))

    def test_draw_image_result(self):
        self._check_result(
            draw_image(x=0, y=0, width=10, height=10, href="data:image/png;base64,")
        )

    def test_draw_group_result(self):
        self._check_result(draw_group(children="<rect/>"))

    def test_draw_raw_svg_result(self):
        self._check_result(draw_raw_svg(svg_fragment="<rect/>"))

    def test_element_id_empty_string_auto_assigns(self):
        result = draw_rect(x=0, y=0, width=5, height=5, element_id="")
        text = result[0]
        assert isinstance(text, str)
        assert text.startswith("Rectangle added (id=el-")

    def test_element_id_explicit_used(self):
        result = draw_circle(cx=5, cy=5, r=3, element_id="my-id")
        assert "id=my-id" in result[0]

    def test_stroke_dasharray_empty_string_omitted(self):
        draw_rect(x=0, y=0, width=10, height=10, stroke_dasharray="")
        assert "stroke-dasharray" not in svg()

    def test_stroke_dasharray_value_applied(self):
        draw_rect(x=0, y=0, width=10, height=10, stroke_dasharray="4,2", element_id="r")
        assert 'stroke-dasharray="4,2"' in svg()


class TestSchemaCompatibility:
    """Verify no anyOf in MCP tool schemas (the main compatibility fix)."""

    def _get_schemas(self):
        import asyncio

        import svg_mcp

        tools = asyncio.run(svg_mcp.mcp.list_tools())
        return {t.name: t.parameters for t in tools}

    def _find_anyof(self, schema, path=""):
        """Recursively find any anyOf occurrences in a schema."""
        issues = []
        if isinstance(schema, dict):
            if "anyOf" in schema:
                issues.append(path)
            for k, v in schema.items():
                issues.extend(self._find_anyof(v, f"{path}.{k}"))
        elif isinstance(schema, list):
            for i, item in enumerate(schema):
                issues.extend(self._find_anyof(item, f"{path}[{i}]"))
        return issues

    def test_no_anyof_in_any_tool_schema(self):
        schemas = self._get_schemas()
        all_issues = []
        for tool_name, schema in schemas.items():
            issues = self._find_anyof(schema)
            for issue in issues:
                all_issues.append(f"{tool_name}{issue}")
        assert (
            all_issues == []
        ), f"Found anyOf in tool schemas (breaks LM Studio/Jan.ai): {all_issues}"

    def test_all_properties_have_simple_types(self):
        schemas = self._get_schemas()
        for tool_name, schema in schemas.items():
            for prop_name, prop_schema in schema.get("properties", {}).items():
                assert "type" in prop_schema or "enum" in prop_schema, (
                    f"{tool_name}.{prop_name} has no 'type' or 'enum' "
                    f"(schema: {prop_schema})"
                )

    def test_tool_count(self):
        """Ensure all 22 tools are registered."""
        import asyncio

        import svg_mcp

        tools = asyncio.run(svg_mcp.mcp.list_tools())
        assert len(tools) == 22


class TestDrawPathArcParams:
    """Tests for the arc convenience params on draw_path (Goal 2c)."""

    def test_arc_produces_path_element(self):
        _draw_path(
            arc_cx=100.0,
            arc_cy=100.0,
            arc_r=50.0,
            arc_start_deg=0.0,
            arc_end_deg=180.0,
            stroke="green",
            element_id="a",
        )
        s = svg()
        assert "<path" in s
        assert 'stroke="green"' in s
        # The arc path d attribute should contain an 'A' (arc) command.
        assert " A" in s or ",A" in s or " A" in s.upper()

    def test_arc_mcp_tool_wrapper(self):
        from svg_mcp.tools.drawing import draw_path

        result = draw_path(
            arc_cx=50.0,
            arc_cy=50.0,
            arc_r=30.0,
            arc_start_deg=0.0,
            arc_end_deg=90.0,
        )
        assert isinstance(result[-1], Image)
        text = result[0]
        assert isinstance(text, str)
        assert "Path added" in text

    def test_arc_and_d_raises(self):
        with pytest.raises(ValueError, match="not both"):
            _draw_path(
                d="M0 0 L10 10",
                arc_cx=50.0,
                arc_cy=50.0,
                arc_r=30.0,
                arc_start_deg=0.0,
                arc_end_deg=90.0,
            )

    def test_partial_arc_params_raises(self):
        with pytest.raises(ValueError, match="together"):
            _draw_path(arc_cx=50.0, arc_cy=50.0, arc_r=30.0)  # missing start/end

    def test_plain_d_still_works(self):
        _draw_path(d="M10 80 L90 80", stroke="purple", element_id="p")
        s = svg()
        assert 'd="M10 80 L90 80"' in s

    def test_arc_cw_param_accepted(self):
        """Clockwise arc should not raise."""
        _draw_path(
            arc_cx=100.0,
            arc_cy=100.0,
            arc_r=40.0,
            arc_start_deg=0.0,
            arc_end_deg=270.0,
            arc_cw=True,
            element_id="arc_cw",
        )
        assert "<path" in svg()
