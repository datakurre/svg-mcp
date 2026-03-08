"""Tools for adding, inspecting, updating, removing elements and defs."""

from __future__ import annotations

from fastmcp.utilities.types import ContentBlock

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp


@mcp.tool
def update_element(
    element_id: str,
    svg_fragment: str,
) -> list[ContentBlock]:
    """Replace the SVG fragment of an existing element in-place, identified by its ID.

    Use ``inspect(what='element', element_id=...)`` first to fetch the current fragment,
    edit it, then call this tool.  The element stays at the same z-position in the stack.
    """
    if _get_canvas().update_element(element_id, svg_fragment):
        return canvas_png_response(f"Element '{element_id}' updated.")
    return canvas_png_response(f"Element '{element_id}' not found — no changes made.")


@mcp.tool
def remove_element(element_id: str) -> list[ContentBlock]:
    """Remove an element from the canvas by its ID."""
    if _get_canvas().remove_element(element_id):
        return canvas_png_response(f"Element '{element_id}' removed.")
    return canvas_png_response(f"Element '{element_id}' not found.")


@mcp.tool
def add_def(def_fragment: str) -> list[ContentBlock]:
    """Add a definition (gradient, pattern, clip-path, filter, etc.) to the <defs> section.

    Example:
        '<linearGradient id="g1"><stop offset="0%" stop-color="red"/>'
        '<stop offset="100%" stop-color="blue"/></linearGradient>'
    """
    _get_canvas().add_def(def_fragment)
    return canvas_png_response("Definition added to <defs>.")
