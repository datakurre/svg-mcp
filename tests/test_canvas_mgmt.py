"""Tests for canvas management MCP tools (canvas_mgmt.py)."""

from mcp import types

from svg_mcp.canvas import Canvas, get_canvas, set_canvas
from svg_mcp.tools.canvas_mgmt import (
    clear_canvas,
    create_canvas,
    export,
    inspect,
    resize_canvas,
)


class TestCreateCanvas:
    def test_returns_content_blocks(self):
        result = create_canvas(width=200, height=150, background="navy")
        assert isinstance(result, list)
        assert any(isinstance(b, types.ImageContent) for b in result)

    def test_sets_dimensions(self):
        create_canvas(width=320, height=240, background="white")
        c = get_canvas()
        assert c.width == 320
        assert c.height == 240

    def test_sets_background(self):
        create_canvas(background="crimson")
        assert get_canvas().background == "crimson"

    def test_resets_elements(self):
        from svg_mcp.tools.drawing import _draw_rect
        _draw_rect(x=0, y=0, width=10, height=10)
        create_canvas()
        assert get_canvas().elements == []

    def test_message_contains_dimensions(self):
        result = create_canvas(width=400, height=300)
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "400" in text.text
        assert "300" in text.text


class TestResizeCanvas:
    def test_changes_dimensions(self):
        resize_canvas(width=1024, height=768)
        c = get_canvas()
        assert c.width == 1024
        assert c.height == 768

    def test_preserves_background_when_empty_string(self):
        get_canvas().background = "gold"
        resize_canvas(width=100, height=100, background="")
        assert get_canvas().background == "gold"

    def test_changes_background_when_provided(self):
        resize_canvas(width=100, height=100, background="teal")
        assert get_canvas().background == "teal"

    def test_preserves_elements(self):
        from svg_mcp.tools.drawing import _draw_rect
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r")
        resize_canvas(width=200, height=200)
        assert any(e["id"] == "r" for e in get_canvas().elements)

    def test_returns_content_blocks(self):
        result = resize_canvas(width=100, height=100)
        assert any(isinstance(b, types.ImageContent) for b in result)


class TestInspect:
    def test_canvas_mode(self):
        result = inspect(what="canvas")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "800" in text.text  # default width
        assert "600" in text.text  # default height

    def test_svg_mode_returns_svg_source(self):
        result = inspect(what="svg")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "<svg" in text.text

    def test_elements_mode_empty(self):
        result = inspect(what="elements")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "empty" in text.text.lower()

    def test_elements_mode_lists_ids(self):
        from svg_mcp.tools.drawing import _draw_rect
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r1")
        result = inspect(what="elements")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "r1" in text.text

    def test_element_mode_returns_fragment(self):
        from svg_mcp.tools.drawing import _draw_rect
        _draw_rect(x=0, y=0, width=10, height=10, element_id="r1")
        result = inspect(what="element", element_id="r1")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "<rect" in text.text

    def test_element_mode_missing_id(self):
        result = inspect(what="element", element_id="")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "element_id" in text.text or "Provide" in text.text

    def test_element_mode_not_found(self):
        result = inspect(what="element", element_id="nonexistent")
        text = next(b for b in result if isinstance(b, types.TextContent))
        assert "not found" in text.text

    def test_always_returns_png(self):
        result = inspect(what="canvas")
        assert any(isinstance(b, types.ImageContent) for b in result)


class TestClearCanvas:
    def test_removes_all_elements(self):
        from svg_mcp.tools.drawing import _draw_rect
        _draw_rect(x=0, y=0, width=10, height=10)
        clear_canvas()
        assert get_canvas().elements == []

    def test_returns_content_blocks(self):
        result = clear_canvas()
        assert any(isinstance(b, types.ImageContent) for b in result)


class TestExport:
    def test_export_svg(self, tmp_path):
        path = str(tmp_path / "out.svg")
        result = export(file_path=path, format="svg")
        with open(path) as f:
            content = f.read()
        assert "<svg" in content
        assert any(isinstance(b, types.ImageContent) for b in result)

    def test_export_png(self, tmp_path):
        path = str(tmp_path / "out.png")
        result = export(file_path=path, format="png")
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"
        assert any(isinstance(b, types.ImageContent) for b in result)

    def test_export_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "out.svg")
        export(file_path=path, format="svg")
        import os
        assert os.path.exists(path)

    def test_export_png_scale(self, tmp_path):
        path1 = str(tmp_path / "small.png")
        path2 = str(tmp_path / "large.png")
        export(file_path=path1, format="png", scale=1.0)
        export(file_path=path2, format="png", scale=2.0)
        import os
        assert os.path.getsize(path2) > os.path.getsize(path1)
