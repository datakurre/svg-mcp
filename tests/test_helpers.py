"""Tests for the _helpers module (canvas_png_response)."""

from fastmcp.utilities.types import Image

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import Canvas, set_canvas


class TestCanvasPngResponse:
    def test_with_message_returns_text_and_image(self):
        result = canvas_png_response("hello")
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert result[0] == "hello"
        assert isinstance(result[1], Image)

    def test_without_message_returns_image_only(self):
        result = canvas_png_response()
        assert len(result) == 1
        assert isinstance(result[0], Image)

    def test_image_is_png(self):
        result = canvas_png_response()
        img = result[0]
        assert isinstance(img, Image)
        assert img._mime_type == "image/png"

    def test_reflects_current_canvas(self):
        """Response PNG changes when the canvas changes."""
        set_canvas(Canvas(width=10, height=10, background="white"))
        before = canvas_png_response()[0].data

        set_canvas(Canvas(width=10, height=10, background="black"))
        after = canvas_png_response()[0].data

        assert before != after
