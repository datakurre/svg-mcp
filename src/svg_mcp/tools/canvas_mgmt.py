"""Tools for creating, configuring, inspecting, and exporting the canvas."""

from __future__ import annotations

import os
from typing import Literal

from fastmcp.utilities.types import ContentBlock

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import (
    _DEFAULT_BG,
    _DEFAULT_HEIGHT,
    _DEFAULT_WIDTH,
    _MAX_SCALE,
    Canvas,
    get_canvas,
    set_canvas,
)
from svg_mcp.server import mcp


@mcp.tool
def create_canvas(
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
    background: str = _DEFAULT_BG,
) -> list[ContentBlock]:
    """Create or reset the canvas with the given dimensions and background colour."""
    c = Canvas(width=width, height=height, background=background)
    set_canvas(c)
    msg = f"Canvas created ({c.width}\u00d7{c.height}, background={background})."
    if c.warnings:
        msg += "\nWarning: " + " ".join(c.warnings)
    return canvas_png_response(msg)


@mcp.tool
def resize_canvas(
    width: int,
    height: int,
    background: str = "",
) -> list[ContentBlock]:
    """Resize the canvas without clearing its elements. Optionally change the background colour."""
    warnings = get_canvas().resize(width, height, background or None)
    c = get_canvas()
    msg = (
        f"Canvas resized to {c.width}\u00d7{c.height}"
        + (f", background={background}" if background else "")
        + "."
    )
    if warnings:
        msg += "\nWarning: " + " ".join(warnings)
    return canvas_png_response(msg)


@mcp.tool
def inspect(
    what: Literal["canvas", "svg", "elements", "element"],
    element_id: str = "",
) -> list[ContentBlock]:
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
        return canvas_png_response(
            "Elements on canvas (bottom → top):\n" + "\n".join(lines)
        )
    # what == "element"
    if not element_id:
        return canvas_png_response("Provide `element_id` when using what='element'.")
    svg = c.get_element_svg(element_id)
    if svg is None:
        return canvas_png_response(f"Element '{element_id}' not found.")
    return canvas_png_response(f"Element '{element_id}':\n```xml\n{svg}\n```")


@mcp.tool
def clear_canvas() -> list[ContentBlock]:
    """Remove all elements (and defs) from the canvas, keeping its size and background."""
    get_canvas().clear()
    return canvas_png_response("Canvas cleared.")


@mcp.tool
def export(
    file_path: str,
    format: Literal["svg", "png"] = "svg",
    scale: float = 1.0,
) -> list[ContentBlock]:
    """Export the current canvas to a file.

    ``format``
    - ``"svg"`` — export as an SVG text file (``scale`` is ignored). **Default.**
    - ``"png"`` — export as a PNG raster image; ``scale`` multiplies the resolution
      (e.g. ``2.0`` for retina/HiDPI output).
    """
    path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    scale_warn = ""
    if scale > _MAX_SCALE:
        scale_warn = f" (scale clamped from {scale} to {_MAX_SCALE})"
        scale = _MAX_SCALE
    elif scale <= 0:
        scale_warn = f" (scale {scale} invalid; using 1.0)"
        scale = 1.0
    if format == "svg":
        with open(path, "w", encoding="utf-8") as f:
            f.write(get_canvas().to_svg())
        return canvas_png_response(f"SVG exported to `{path}`{scale_warn}.")
    # format == "png"
    with open(path, "wb") as f:
        f.write(get_canvas().to_png_bytes(scale=scale))
    return canvas_png_response(f"PNG exported to `{path}` (scale={scale}){scale_warn}.")
