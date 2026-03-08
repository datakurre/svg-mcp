"""Tests for element management MCP tools (elements.py) and z-order (zorder.py)."""

from fastmcp.utilities.types import Image

from svg_mcp.canvas import get_canvas
from svg_mcp.tools.drawing import _draw_rect
from svg_mcp.tools.elements import add_def, remove_element, update_element
from svg_mcp.tools.zorder import reorder_element


class TestUpdateElement:
    def test_updates_svg_fragment(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        update_element(element_id="r", svg_fragment='<circle cx="5" cy="5" r="5"/>')
        assert get_canvas().get_element_svg("r") == '<circle cx="5" cy="5" r="5"/>'

    def test_returns_success_message(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        result = update_element(element_id="r", svg_fragment="<new/>")
        text = next(b for b in result if isinstance(b, str))
        assert "updated" in text

    def test_returns_not_found_for_missing(self):
        result = update_element(element_id="ghost", svg_fragment="<x/>")
        text = next(b for b in result if isinstance(b, str))
        assert "not found" in text

    def test_always_returns_png(self):
        result = update_element(element_id="ghost", svg_fragment="<x/>")
        assert any(isinstance(b, Image) for b in result)


class TestRemoveElement:
    def test_removes_element(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        remove_element(element_id="r")
        assert get_canvas().get_element_svg("r") is None

    def test_returns_success_message(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        result = remove_element(element_id="r")
        text = next(b for b in result if isinstance(b, str))
        assert "removed" in text

    def test_returns_not_found_for_missing(self):
        result = remove_element(element_id="ghost")
        text = next(b for b in result if isinstance(b, str))
        assert "not found" in text

    def test_always_returns_png(self):
        result = remove_element(element_id="ghost")
        assert any(isinstance(b, Image) for b in result)


class TestAddDef:
    def test_appends_to_defs(self):
        add_def(def_fragment='<linearGradient id="g"/>')
        assert any("linearGradient" in d for d in get_canvas().defs)

    def test_def_appears_in_svg(self):
        add_def(def_fragment='<linearGradient id="g"/>')
        svg = get_canvas().to_svg()
        assert "<defs>" in svg
        assert "linearGradient" in svg

    def test_returns_content_blocks(self):
        result = add_def(def_fragment="<filter/>")
        assert any(isinstance(b, Image) for b in result)


class TestReorderElement:
    def _setup(self):
        for name in ["a", "b", "c"]:
            _draw_rect(x=0, y=0, width=1, height=1, element_id=name)

    def _order(self):
        return [e["id"] for e in get_canvas().elements]

    def test_forward(self):
        self._setup()
        reorder_element(element_id="a", direction="forward")
        assert self._order() == ["b", "a", "c"]

    def test_backward(self):
        self._setup()
        reorder_element(element_id="c", direction="backward")
        assert self._order() == ["a", "c", "b"]

    def test_front(self):
        self._setup()
        reorder_element(element_id="a", direction="front")
        assert self._order()[-1] == "a"

    def test_back(self):
        self._setup()
        reorder_element(element_id="c", direction="back")
        assert self._order()[0] == "c"

    def test_not_found_message(self):
        self._setup()
        result = reorder_element(element_id="ghost", direction="forward")
        text = next(b for b in result if isinstance(b, str))
        assert "not found" in text or "limit" in text

    def test_always_returns_png(self):
        self._setup()
        result = reorder_element(element_id="a", direction="front")
        assert any(isinstance(b, Image) for b in result)


class TestAddDefTypedMode:
    """Tests for add_def kind/params typed API (Goal 2d)."""

    def test_linear_gradient_creates_def(self):
        add_def(
            kind="linear_gradient",
            def_id="lg1",
            params='{"x1":0,"y1":0,"x2":1,"y2":0,"stops":[{"offset":0,"color":"red"},{"offset":1,"color":"blue"}]}',
        )
        svg = get_canvas().to_svg()
        assert "linearGradient" in svg
        assert 'id="lg1"' in svg
        assert "red" in svg
        assert "blue" in svg

    def test_radial_gradient_creates_def(self):
        add_def(
            kind="radial_gradient",
            def_id="rg1",
            params='{"cx":0.5,"cy":0.5,"r":0.5,"stops":[{"offset":0,"color":"yellow"},{"offset":1,"color":"green"}]}',
        )
        svg = get_canvas().to_svg()
        assert "radialGradient" in svg
        assert 'id="rg1"' in svg

    def test_clip_path_creates_def(self):
        add_def(
            kind="clip_path",
            def_id="cp1",
            params='{"content":"<rect x=\\"0\\" y=\\"0\\" width=\\"100\\" height=\\"100\\"/>"}',
        )
        svg = get_canvas().to_svg()
        assert "clipPath" in svg
        assert 'id="cp1"' in svg

    def test_pattern_creates_def(self):
        add_def(
            kind="pattern",
            def_id="pat1",
            params='{"x":0,"y":0,"width":10,"height":10}',
        )
        svg = get_canvas().to_svg()
        assert "pattern" in svg
        assert 'id="pat1"' in svg

    def test_marker_creates_def(self):
        add_def(
            kind="marker",
            def_id="m1",
            params='{"min_x":-0.1,"min_y":-0.5,"width":1.0,"height":1.0,"scale":4,"orient":"auto"}',
        )
        svg = get_canvas().to_svg()
        assert "marker" in svg
        assert 'id="m1"' in svg

    def test_raw_fallthrough_without_kind(self):
        add_def(def_fragment='<filter id="f1"/>')
        assert any("filter" in d for d in get_canvas().defs)

    def test_returns_image(self):
        result = add_def(kind="linear_gradient", def_id="x", params='{"stops":[]}')
        assert any(isinstance(b, Image) for b in result)
