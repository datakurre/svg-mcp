"""Tools for controlling the z-order (stacking order) of canvas elements."""

from __future__ import annotations

from mcp import types

import svg_mcp.canvas as _state
from svg_mcp._helpers import canvas_png_response
from svg_mcp.server import mcp


@mcp.tool()
def bring_forward(element_id: str) -> list[types.ContentBlock]:
    """Move an element one step forward in the z-order (rendered later = on top)."""
    if _state.canvas.move_element(element_id, +1):
        return canvas_png_response(f"'{element_id}' moved forward.")
    return canvas_png_response(f"'{element_id}' not found or already at the top.")


@mcp.tool()
def send_backward(element_id: str) -> list[types.ContentBlock]:
    """Move an element one step backward in the z-order (rendered earlier = behind)."""
    if _state.canvas.move_element(element_id, -1):
        return canvas_png_response(f"'{element_id}' moved backward.")
    return canvas_png_response(f"'{element_id}' not found or already at the bottom.")


@mcp.tool()
def bring_to_front(element_id: str) -> list[types.ContentBlock]:
    """Move an element to the very top of the z-order (in front of everything)."""
    n = len(_state.canvas.elements)
    if _state.canvas.move_element(element_id, n):
        return canvas_png_response(f"'{element_id}' brought to front.")
    return canvas_png_response(f"'{element_id}' not found or already at the front.")


@mcp.tool()
def send_to_back(element_id: str) -> list[types.ContentBlock]:
    """Move an element to the very bottom of the z-order (behind everything)."""
    n = len(_state.canvas.elements)
    if _state.canvas.move_element(element_id, -n):
        return canvas_png_response(f"'{element_id}' sent to back.")
    return canvas_png_response(f"'{element_id}' not found or already at the back.")
