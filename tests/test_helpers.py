"""Tests for the _helpers module (style_attrs, canvas_png_response)."""

from mcp.types import ImageContent, TextContent

from svg_mcp._helpers import canvas_png_response, style_attrs
from svg_mcp.canvas import Canvas, set_canvas


class TestStyleAttrs:
    def test_empty_returns_empty_string(self):
        assert style_attrs() == ""

    def test_fill_only(self):
        result = style_attrs(fill="red")
        assert 'fill="red"' in result

    def test_stroke_and_width(self):
        result = style_attrs(stroke="blue", stroke_width=2.5)
        assert 'stroke="blue"' in result
        assert 'stroke-width="2.5"' in result

    def test_stroke_dasharray(self):
        result = style_attrs(stroke_dasharray="5,3")
        assert 'stroke-dasharray="5,3"' in result

    def test_opacity(self):
        result = style_attrs(opacity=0.5)
        assert 'opacity="0.5"' in result

    def test_extra_attrs(self):
        result = style_attrs(extra={"font-size": "16", "text-anchor": "middle"})
        assert 'font-size="16"' in result
        assert 'text-anchor="middle"' in result

    def test_none_values_omitted(self):
        result = style_attrs(fill=None, stroke=None, stroke_dasharray=None)
        assert result == ""

    def test_all_params(self):
        result = style_attrs(
            fill="red",
            stroke="black",
            stroke_width=1,
            opacity=0.8,
            stroke_dasharray="4,2",
            extra={"font-family": "serif"},
        )
        assert 'fill="red"' in result
        assert 'stroke="black"' in result
        assert 'stroke-width="1"' in result
        assert 'opacity="0.8"' in result
        assert 'stroke-dasharray="4,2"' in result
        assert 'font-family="serif"' in result


class TestCanvasPngResponse:
    def test_with_message_returns_text_and_image(self):
        result = canvas_png_response("hello")
        assert len(result) == 2
        assert isinstance(result[0], TextContent)
        assert result[0].text == "hello"
        assert isinstance(result[1], ImageContent)

    def test_without_message_returns_image_only(self):
        result = canvas_png_response()
        assert len(result) == 1
        assert isinstance(result[0], ImageContent)

    def test_image_is_png(self):
        result = canvas_png_response()
        img = result[0]
        assert img.mimeType == "image/png"

    def test_reflects_current_canvas(self):
        """Response PNG changes when the canvas changes."""
        import base64

        set_canvas(Canvas(width=10, height=10, background="white"))
        before = canvas_png_response()[0].data

        set_canvas(Canvas(width=10, height=10, background="black"))
        after = canvas_png_response()[0].data

        assert before != after
