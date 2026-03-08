"""Tools for creating, configuring, inspecting, and exporting the canvas."""

from __future__ import annotations

import os
from typing import Literal

from mcp import types

import svg_mcp.canvas as _state
from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import Canvas, _DEFAULT_BG, _DEFAULT_HEIGHT, _DEFAULT_WIDTH, get_canvas, set_canvas
from svg_mcp.server import mcp


@mcp.tool(structured_output=False)
def create_canvas(
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
    background: str = _DEFAULT_BG,
) -> list[types.ContentBlock]:
    """Create or reset the canvas with the given dimensions and background colour."""
    set_canvas(Canvas(width=width, height=height, background=background))
    return canvas_png_response(
        f"Canvas created ({width}×{height}, background={background})."
    )


@mcp.tool(structured_output=False)
def resize_canvas(
    width: int,
    height: int,
    background: str = "",
) -> list[types.ContentBlock]:
    """Resize the canvas without clearing its elements. Optionally change the background colour."""
    get_canvas().resize(width, height, background or None)
    return canvas_png_response(
        f"Canvas resized to {width}×{height}"
        + (f", background={background}" if background else "") + "."
    )


@mcp.tool(structured_output=False)
def inspect(
    what: Literal["canvas", "svg", "elements", "element"],
    element_id: str = "",
) -> list[types.ContentBlock]:
    """Inspect the current canvas state.

    ``what`` must be one of:
    - ``"canvas"``   — render a PNG preview with canvas dimensions and element count.
    - ``"svg"``      — return the raw SVG source of the entire canvas.
    - ``"elements"`` — list all element IDs in z-order (bottom → top).
    - ``"element"``  — return the raw SVG fragment for the element given by ``element_id``.
    """
    c = get_canvas()
    if what == "canvas":
        return canvas_png_response(
            f"Canvas: {c.width}×{c.height}, background={c.background}, "
            f"{len(c.elements)} element(s)."
        )
    if what == "svg":
        return canvas_png_response(f"```xml\n{c.to_svg()}\n```")
    if what == "elements":
        if not c.elements:
            return canvas_png_response("Canvas is empty — no elements.")
        lines = [f"{i + 1}. {e['id']}" for i, e in enumerate(c.elements)]
        return canvas_png_response("Elements on canvas (bottom → top):\n" + "\n".join(lines))
    # what == "element"
    if not element_id:
        return canvas_png_response("Provide `element_id` when using what='element'.")
    svg = c.get_element_svg(element_id)
    if svg is None:
        return canvas_png_response(f"Element '{element_id}' not found.")
    return canvas_png_response(f"Element '{element_id}':\n```xml\n{svg}\n```")


@mcp.tool(structured_output=False)
def clear_canvas() -> list[types.ContentBlock]:
    """Remove all elements (and defs) from the canvas, keeping its size and background."""
    get_canvas().clear()
    return canvas_png_response("Canvas cleared.")


@mcp.tool(structured_output=False)
def export(
    file_path: str,
    format: Literal["svg", "png"] = "svg",
    scale: float = 1.0,
) -> list[types.ContentBlock]:
    """Export the current canvas to a file.

    ``format``
    - ``"svg"`` — export as an SVG text file (``scale`` is ignored). **Default.**
    - ``"png"`` — export as a PNG raster image; ``scale`` multiplies the resolution
      (e.g. ``2.0`` for retina/HiDPI output).
    """
    path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if format == "svg":
        with open(path, "w", encoding="utf-8") as f:
            f.write(get_canvas().to_svg())
        return canvas_png_response(f"SVG exported to `{path}`.")
    # format == "png"
    with open(path, "wb") as f:
        f.write(get_canvas().to_png_bytes(scale=scale))
    return canvas_png_response(f"PNG exported to `{path}` (scale={scale}).")
