"""Tests for canvas management MCP tools (canvas_mgmt.py)."""

from fastmcp.utilities.types import Image

from svg_mcp.canvas import (
    _MAX_DIMENSION,
    _MAX_SCALE,
    _MIN_DIMENSION,
    Canvas,
    get_canvas,
    set_canvas,
)
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
        assert any(isinstance(b, Image) for b in result)

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
        text = next(b for b in result if isinstance(b, str))
        assert "400" in text
        assert "300" in text


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
        assert any(isinstance(b, Image) for b in result)


class TestInspect:
    def test_canvas_mode(self):
        result = inspect(what="canvas")
        text = next(b for b in result if isinstance(b, str))
        assert "800" in text  # default width
        assert "600" in text  # default height

    def test_svg_mode_returns_svg_source(self):
        result = inspect(what="svg")
        text = next(b for b in result if isinstance(b, str))
        assert "<svg" in text

    def test_elements_mode_empty(self):
        result = inspect(what="elements")
        text = next(b for b in result if isinstance(b, str))
        assert "empty" in text.lower()

    def test_elements_mode_lists_ids(self):
        from svg_mcp.tools.drawing import _draw_rect

        _draw_rect(x=0, y=0, width=10, height=10, element_id="r1")
        result = inspect(what="elements")
        text = next(b for b in result if isinstance(b, str))
        assert "r1" in text

    def test_element_mode_returns_fragment(self):
        from svg_mcp.tools.drawing import _draw_rect

        _draw_rect(x=0, y=0, width=10, height=10, element_id="r1")
        result = inspect(what="element", element_id="r1")
        text = next(b for b in result if isinstance(b, str))
        assert "<rect" in text

    def test_element_mode_missing_id(self):
        result = inspect(what="element", element_id="")
        text = next(b for b in result if isinstance(b, str))
        assert "element_id" in text or "Provide" in text

    def test_element_mode_not_found(self):
        result = inspect(what="element", element_id="nonexistent")
        text = next(b for b in result if isinstance(b, str))
        assert "not found" in text

    def test_always_returns_png(self):
        result = inspect(what="canvas")
        assert any(isinstance(b, Image) for b in result)


class TestClearCanvas:
    def test_removes_all_elements(self):
        from svg_mcp.tools.drawing import _draw_rect

        _draw_rect(x=0, y=0, width=10, height=10)
        clear_canvas()
        assert get_canvas().elements == []

    def test_returns_content_blocks(self):
        result = clear_canvas()
        assert any(isinstance(b, Image) for b in result)


class TestExport:
    def test_export_svg(self, tmp_path):
        path = str(tmp_path / "out.svg")
        result = export(file_path=path, format="svg")
        with open(path) as f:
            content = f.read()
        assert "<svg" in content
        assert any(isinstance(b, Image) for b in result)

    def test_export_png(self, tmp_path):
        path = str(tmp_path / "out.png")
        result = export(file_path=path, format="png")
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"
        assert any(isinstance(b, Image) for b in result)

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


class TestCanvasSizeClamping:
    """Verify that unreasonable canvas dimensions are clamped, not crash-inducing."""

    def test_create_canvas_clamps_huge_width(self):
        # When width is unreasonably large the canvas should fall back to a
        # 4:3 canvas at MAX width, regardless of the requested height.
        _expected_h = _MAX_DIMENSION * 3 // 4
        result = create_canvas(width=400_000_000, height=600)
        c = get_canvas()
        assert c.width == _MAX_DIMENSION
        assert c.height == _expected_h
        text = next(b for b in result if isinstance(b, str))
        assert "clamped" in text.lower() or str(_MAX_DIMENSION) in text

    def test_create_canvas_clamps_huge_height(self):
        # When height is unreasonably large the canvas falls back to 4:3 at MAX width.
        create_canvas(width=800, height=400_000_000)
        c = get_canvas()
        assert c.width == _MAX_DIMENSION
        assert c.height == _MAX_DIMENSION * 3 // 4

    def test_create_canvas_clamps_both_dimensions(self):
        create_canvas(width=999_999_999, height=999_999_999)
        c = get_canvas()
        assert c.width == _MAX_DIMENSION
        assert c.height == _MAX_DIMENSION * 3 // 4

    def test_create_canvas_clamps_zero_width(self):
        create_canvas(width=0, height=100)
        assert get_canvas().width == _MIN_DIMENSION

    def test_create_canvas_clamps_negative_dimension(self):
        create_canvas(width=-50, height=100)
        assert get_canvas().width == _MIN_DIMENSION

    def test_create_canvas_normal_sizes_unchanged(self):
        create_canvas(width=1920, height=1080)
        c = get_canvas()
        assert c.width == 1920
        assert c.height == 1080

    def test_resize_canvas_clamps_huge_dimension(self):
        result = resize_canvas(width=400_000_000, height=600)
        c = get_canvas()
        assert c.width == _MAX_DIMENSION
        assert c.height == _MAX_DIMENSION * 3 // 4
        text = next(b for b in result if isinstance(b, str))
        assert "clamped" in text.lower() or str(_MAX_DIMENSION) in text

    def test_resize_canvas_clamps_zero(self):
        resize_canvas(width=0, height=0)
        c = get_canvas()
        assert c.width == _MIN_DIMENSION
        assert c.height == _MIN_DIMENSION

    def test_export_scale_clamped(self, tmp_path):
        path = str(tmp_path / "out.png")
        result = export(file_path=path, format="png", scale=1000.0)
        text = next(b for b in result if isinstance(b, str))
        assert "clamped" in text.lower()

    def test_export_zero_scale_corrected(self, tmp_path):
        path = str(tmp_path / "out.png")
        result = export(file_path=path, format="png", scale=0.0)
        text = next(b for b in result if isinstance(b, str))
        assert "invalid" in text.lower() or "1.0" in text

    def test_export_valid_scale_unchanged(self, tmp_path):
        path = str(tmp_path / "out.png")
        result = export(file_path=path, format="png", scale=2.0)
        text = next(b for b in result if isinstance(b, str))
        assert "clamped" not in text.lower()

    def test_canvas_warnings_attribute_set(self):
        c = Canvas(width=400_000_000, height=600)
        # Expects at least: one "clamped" warning + one 4:3 adjustment warning.
        assert len(c.warnings) >= 2
        assert "width" in c.warnings[0]

    def test_canvas_no_warnings_for_normal_size(self):
        c = Canvas(width=800, height=600)
        assert c.warnings == []
