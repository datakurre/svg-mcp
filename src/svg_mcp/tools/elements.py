"""Tools for adding, inspecting, updating, removing elements and defs."""

from __future__ import annotations

from mcp import types

import svg_mcp.canvas as _state
from svg_mcp._helpers import canvas_png_response
from svg_mcp.server import mcp


@mcp.tool()
def list_elements() -> list[types.ContentBlock]:
    """List all element IDs currently on the canvas (in z-order, bottom to top)."""
    if not _state.canvas.elements:
        return canvas_png_response("Canvas is empty — no elements.")
    lines = [f"{i + 1}. {e['id']}" for i, e in enumerate(_state.canvas.elements)]
    return canvas_png_response("Elements on canvas (bottom → top):\n" + "\n".join(lines))


@mcp.tool()
def get_element(element_id: str) -> list[types.ContentBlock]:
    """Return the raw SVG fragment for a single element on the canvas."""
    svg = _state.canvas.get_element_svg(element_id)
    if svg is None:
        return canvas_png_response(f"Element '{element_id}' not found.")
    return canvas_png_response(f"Element '{element_id}':\n```xml\n{svg}\n```")


@mcp.tool()
def update_element(
    element_id: str,
    svg_fragment: str,
) -> list[types.ContentBlock]:
    """Replace the SVG fragment of an existing element in-place, identified by its ID.

    Use `get_element` first to fetch the current fragment, edit it, then call this tool.
    The element stays at the same z-position in the stack.
    """
    if _state.canvas.update_element(element_id, svg_fragment):
        return canvas_png_response(f"Element '{element_id}' updated.")
    return canvas_png_response(f"Element '{element_id}' not found — no changes made.")


@mcp.tool()
def remove_element(element_id: str) -> list[types.ContentBlock]:
    """Remove an element from the canvas by its ID."""
    if _state.canvas.remove_element(element_id):
        return canvas_png_response(f"Element '{element_id}' removed.")
    return canvas_png_response(f"Element '{element_id}' not found.")


@mcp.tool()
def add_def(def_fragment: str) -> list[types.ContentBlock]:
    """Add a definition (gradient, pattern, clip-path, filter, etc.) to the <defs> section.

    Example:
        '<linearGradient id="g1"><stop offset="0%" stop-color="red"/>'
        '<stop offset="100%" stop-color="blue"/></linearGradient>'
    """
    _state.canvas.add_def(def_fragment)
    return canvas_png_response("Definition added to <defs>.")
