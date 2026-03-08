"""Tests for the batch MCP tool."""

from fastmcp.utilities.types import Image

from svg_mcp.canvas import Canvas, get_canvas, set_canvas
from svg_mcp.tools.batch import _dispatch, batch

# ---------------------------------------------------------------------------
# _dispatch — internal unit tests
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_draw_rect(self):
        msg = _dispatch("draw_rect", {"x": 0, "y": 0, "width": 10, "height": 10})
        assert "Rectangle added" in msg

    def test_draw_circle(self):
        msg = _dispatch("draw_circle", {"cx": 5, "cy": 5, "r": 3})
        assert "Circle added" in msg

    def test_draw_ellipse(self):
        msg = _dispatch("draw_ellipse", {"cx": 5, "cy": 5, "rx": 4, "ry": 2})
        assert "Ellipse added" in msg

    def test_draw_line(self):
        msg = _dispatch("draw_line", {"x1": 0, "y1": 0, "x2": 10, "y2": 10})
        assert "Line added" in msg

    def test_draw_polyline(self):
        msg = _dispatch("draw_polyline", {"points": "0,0 10,10"})
        assert "Polyline added" in msg

    def test_draw_polygon(self):
        msg = _dispatch("draw_polygon", {"points": "0,0 10,0 5,10"})
        assert "Polygon added" in msg

    def test_draw_path(self):
        msg = _dispatch("draw_path", {"d": "M0 0 L10 10"})
        assert "Path added" in msg

    def test_draw_text(self):
        msg = _dispatch("draw_text", {"x": 0, "y": 10, "text": "Hi"})
        assert "Text added" in msg

    def test_draw_image(self):
        msg = _dispatch(
            "draw_image",
            {
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "href": "data:image/png;base64,",
            },
        )
        assert "Image added" in msg

    def test_draw_group(self):
        msg = _dispatch("draw_group", {"children": "<rect/>"})
        assert "Group added" in msg

    def test_draw_raw_svg(self):
        msg = _dispatch("draw_raw_svg", {"svg_fragment": "<use/>"})
        assert "Raw SVG added" in msg

    def test_update_element_found(self):
        _dispatch(
            "draw_rect", {"x": 0, "y": 0, "width": 5, "height": 5, "element_id": "r"}
        )
        msg = _dispatch("update_element", {"element_id": "r", "svg_fragment": "<new/>"})
        assert "updated" in msg

    def test_update_element_not_found(self):
        msg = _dispatch(
            "update_element", {"element_id": "ghost", "svg_fragment": "<x/>"}
        )
        assert "not found" in msg

    def test_remove_element_found(self):
        _dispatch(
            "draw_rect", {"x": 0, "y": 0, "width": 5, "height": 5, "element_id": "r"}
        )
        msg = _dispatch("remove_element", {"element_id": "r"})
        assert "removed" in msg

    def test_remove_element_not_found(self):
        msg = _dispatch("remove_element", {"element_id": "ghost"})
        assert "not found" in msg

    def test_add_def(self):
        msg = _dispatch("add_def", {"def_fragment": "<filter/>"})
        assert "Definition added" in msg

    def test_reorder_element_forward(self):
        _dispatch(
            "draw_rect", {"x": 0, "y": 0, "width": 1, "height": 1, "element_id": "a"}
        )
        _dispatch(
            "draw_rect", {"x": 0, "y": 0, "width": 1, "height": 1, "element_id": "b"}
        )
        msg = _dispatch("reorder_element", {"element_id": "a", "direction": "forward"})
        assert "moved forward" in msg

    def test_create_canvas(self):
        msg = _dispatch(
            "create_canvas", {"width": 100, "height": 50, "background": "red"}
        )
        assert "Canvas created" in msg
        c = get_canvas()
        assert c.width == 100
        assert c.height == 50

    def test_resize_canvas(self):
        msg = _dispatch("resize_canvas", {"width": 200, "height": 150})
        assert "resized" in msg
        assert get_canvas().width == 200

    def test_clear_canvas(self):
        _dispatch("draw_rect", {"x": 0, "y": 0, "width": 5, "height": 5})
        msg = _dispatch("clear_canvas", {})
        assert "cleared" in msg
        assert get_canvas().elements == []

    def test_history_undo(self):
        _dispatch("draw_rect", {"x": 0, "y": 0, "width": 5, "height": 5})
        msg = _dispatch("history", {"action": "undo"})
        assert "Undo" in msg

    def test_history_redo(self):
        _dispatch("draw_rect", {"x": 0, "y": 0, "width": 5, "height": 5})
        _dispatch("history", {"action": "undo"})
        msg = _dispatch("history", {"action": "redo"})
        assert "Redo" in msg

    def test_unknown_tool_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown tool"):
            _dispatch("nonexistent_tool", {})


# ---------------------------------------------------------------------------
# batch MCP tool
# ---------------------------------------------------------------------------


class TestBatch:
    def test_returns_content_blocks(self):
        result = batch(
            calls=[
                {
                    "tool": "draw_rect",
                    "args": {"x": 0, "y": 0, "width": 10, "height": 10},
                },
            ]
        )
        assert isinstance(result, list)
        assert any(isinstance(b, Image) for b in result)

    def test_executes_all_operations(self):
        batch(
            calls=[
                {
                    "tool": "draw_rect",
                    "args": {
                        "x": 0,
                        "y": 0,
                        "width": 5,
                        "height": 5,
                        "element_id": "r",
                    },
                },
                {
                    "tool": "draw_circle",
                    "args": {"cx": 10, "cy": 10, "r": 5, "element_id": "c"},
                },
            ]
        )
        ids = [e["id"] for e in get_canvas().elements]
        assert "r" in ids
        assert "c" in ids

    def test_reports_each_step_in_message(self):
        result = batch(
            calls=[
                {
                    "tool": "draw_rect",
                    "args": {"x": 0, "y": 0, "width": 5, "height": 5},
                },
                {"tool": "draw_circle", "args": {"cx": 5, "cy": 5, "r": 3}},
            ]
        )
        text = next(b for b in result if isinstance(b, str))
        assert "2 operation(s)" in text
        assert "Rectangle added" in text
        assert "Circle added" in text

    def test_error_reported_not_raised(self):
        result = batch(
            calls=[
                {"tool": "unknown_tool", "args": {}},
            ]
        )
        text = next(b for b in result if isinstance(b, str))
        assert "Errors" in text or "error" in text.lower()

    def test_partial_failure_continues(self):
        """A bad step must not prevent subsequent steps from executing."""
        result = batch(
            calls=[
                {"tool": "bad_tool", "args": {}},
                {
                    "tool": "draw_rect",
                    "args": {
                        "x": 0,
                        "y": 0,
                        "width": 5,
                        "height": 5,
                        "element_id": "r",
                    },
                },
            ]
        )
        assert any(e["id"] == "r" for e in get_canvas().elements)
        text = next(b for b in result if isinstance(b, str))
        assert "Rectangle added" in text

    def test_empty_calls_list(self):
        result = batch(calls=[])
        assert any(isinstance(b, Image) for b in result)
        text = next(b for b in result if isinstance(b, str))
        assert "0 operation(s)" in text

    def test_create_canvas_in_batch(self):
        batch(
            calls=[
                {
                    "tool": "create_canvas",
                    "args": {"width": 50, "height": 50, "background": "lime"},
                },
            ]
        )
        c = get_canvas()
        assert c.width == 50
        assert c.background == "lime"

    def test_full_workflow(self):
        """End-to-end: create, draw, inspect, undo in a single batch."""
        batch(
            calls=[
                {"tool": "create_canvas", "args": {"width": 200, "height": 200}},
                {
                    "tool": "draw_rect",
                    "args": {
                        "x": 10,
                        "y": 10,
                        "width": 180,
                        "height": 180,
                        "fill": "skyblue",
                        "element_id": "bg",
                    },
                },
                {
                    "tool": "draw_text",
                    "args": {
                        "x": 100,
                        "y": 110,
                        "text": "Hi",
                        "text_anchor": "middle",
                        "element_id": "lbl",
                    },
                },
            ]
        )
        c = get_canvas()
        assert c.width == 200
        assert any(e["id"] == "bg" for e in c.elements)
        assert any(e["id"] == "lbl" for e in c.elements)
        svg = c.to_svg()
        assert "skyblue" in svg
        assert "Hi" in svg
