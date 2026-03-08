"""Shared response builder and SVG attribute helpers."""

from __future__ import annotations

from fastmcp.utilities.types import Image

from svg_mcp.canvas import get_canvas


def canvas_png_response(message: str = "") -> list[str | Image]:
    """Return a text block (optional) followed by the current canvas as a PNG.

    Always calls ``get_canvas()`` at call-time so that a canvas replacement
    (e.g. via ``create_canvas``) is immediately reflected in the preview.
    """
    blocks: list[str | Image] = []
    if message:
        blocks.append(message)
    blocks.append(Image(data=get_canvas().to_png_bytes(), format="png"))
    return blocks
