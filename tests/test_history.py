"""Tests for history (undo/redo) MCP tool."""

from fastmcp.utilities.types import Image

from svg_mcp.canvas import get_canvas
from svg_mcp.tools.drawing import _draw_rect
from svg_mcp.tools.history import history


class TestHistoryTool:
    def test_undo_reverses_last_draw(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        history(action="undo")
        assert get_canvas().elements == []

    def test_redo_reapplies(self):
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        history(action="undo")
        history(action="redo")
        assert len(get_canvas().elements) == 1

    def test_undo_returns_success_message(self):
        _draw_rect(x=0, y=0, width=10, height=10)
        result = history(action="undo")
        text = next(b for b in result if isinstance(b, str))
        assert "Undo successful" in text

    def test_undo_nothing_to_undo(self):
        result = history(action="undo")
        text = next(b for b in result if isinstance(b, str))
        assert "Nothing to undo" in text

    def test_redo_returns_success_message(self):
        _draw_rect(x=0, y=0, width=10, height=10)
        history(action="undo")
        result = history(action="redo")
        text = next(b for b in result if isinstance(b, str))
        assert "Redo successful" in text

    def test_redo_nothing_to_redo(self):
        result = history(action="redo")
        text = next(b for b in result if isinstance(b, str))
        assert "Nothing to redo" in text

    def test_always_returns_png(self):
        result = history(action="undo")
        assert any(isinstance(b, Image) for b in result)
