"""Tools for creating, configuring, inspecting, and exporting the canvas."""

from __future__ import annotations

import os

from mcp import types

import svg_mcp.canvas as _state
from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import Canvas, _DEFAULT_BG, _DEFAULT_HEIGHT, _DEFAULT_WIDTH
from svg_mcp.server import mcp


@mcp.tool()
def create_canvas(
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
    background: str = _DEFAULT_BG,
) -> list[types.ContentBlock]:
    """Create or reset the canvas with the given dimensions and background colour."""
    _state.canvas = Canvas(width=width, height=height, background=background)
    return canvas_png_response(
        f"Canvas created ({width}×{height}, background={background})."
    )


@mcp.tool()
def resize_canvas(
    width: int,
    height: int,
    background: str | None = None,
) -> list[types.ContentBlock]:
    """Resize the canvas without clearing its elements. Optionally change the background colour."""
    _state.canvas.resize(width, height, background)
    return canvas_png_response(
        f"Canvas resized to {width}×{height}"
        + (f", background={background}" if background else "") + "."
    )


@mcp.tool()
def get_canvas() -> list[types.ContentBlock]:
    """Return the current canvas as a PNG preview (no changes)."""
    c = _state.canvas
    return canvas_png_response(
        f"Canvas: {c.width}×{c.height}, background={c.background}, "
        f"{len(c.elements)} element(s)."
    )


@mcp.tool()
def get_svg_source() -> list[types.ContentBlock]:
    """Return the raw SVG source of the current canvas."""
    return canvas_png_response(f"```xml\n{_state.canvas.to_svg()}\n```")


@mcp.tool()
def clear_canvas() -> list[types.ContentBlock]:
    """Remove all elements (and defs) from the canvas, keeping its size and background."""
    _state.canvas.clear()
    return canvas_png_response("Canvas cleared.")


@mcp.tool()
def export_svg(file_path: str) -> list[types.ContentBlock]:
    """Export the current canvas to an SVG file."""
    path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_state.canvas.to_svg())
    return canvas_png_response(f"SVG exported to `{path}`.")


@mcp.tool()
def export_png(file_path: str, scale: float = 1.0) -> list[types.ContentBlock]:
    """Export the current canvas to a PNG file.

    `scale` multiplies the output resolution (e.g. 2.0 for retina).
    """
    path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(_state.canvas.to_png_bytes(scale=scale))
    return canvas_png_response(f"PNG exported to `{path}` (scale={scale}).")
