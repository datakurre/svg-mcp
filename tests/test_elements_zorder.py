"""Tests for element management MCP tools (elements.py) and z-order (zorder.py)."""

from mcp.types import ImageContent, TextContent

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
        text = next(b for b in result if isinstance(b, TextContent))
        assert "updated" in text.text

    def test_returns_not_found_for_missing(self):
        result = update_element(element_id="ghost", svg_fragment="<x/>")
        text = next(b for b in result if isinstance(b, TextContent))
        assert "not found" in text.text

    def test_always_returns_png(self):
        result = update_element(element_id="ghost", svg_fragment="<x/>")
        assert any(isinstance(b, ImageContent) for b in result)


class TestRemoveElement:
    def test_removes_element(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        remove_element(element_id="r")
        assert get_canvas().get_element_svg("r") is None

    def test_returns_success_message(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        result = remove_element(element_id="r")
        text = next(b for b in result if isinstance(b, TextContent))
        assert "removed" in text.text

    def test_returns_not_found_for_missing(self):
        result = remove_element(element_id="ghost")
        text = next(b for b in result if isinstance(b, TextContent))
        assert "not found" in text.text

    def test_always_returns_png(self):
        result = remove_element(element_id="ghost")
        assert any(isinstance(b, ImageContent) for b in result)


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
        assert any(isinstance(b, ImageContent) for b in result)


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
        text = next(b for b in result if isinstance(b, TextContent))
        assert "not found" in text.text or "limit" in text.text

    def test_always_returns_png(self):
        self._setup()
        result = reorder_element(element_id="a", direction="front")
        assert any(isinstance(b, ImageContent) for b in result)
