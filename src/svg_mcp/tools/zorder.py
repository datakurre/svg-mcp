"""Tool for controlling the z-order (stacking order) of canvas elements."""

from __future__ import annotations

from typing import Literal

from mcp import types

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp


@mcp.tool()
def reorder_element(
    element_id: str,
    direction: Literal["forward", "backward", "front", "back"],
) -> list[types.ContentBlock]:
    """Change the z-order (stacking position) of a canvas element.

    ``direction`` must be one of:
    - ``"forward"``  — move one step toward the top (rendered later = on top).
    - ``"backward"`` — move one step toward the bottom (rendered earlier = behind).
    - ``"front"``    — jump to the very top (in front of everything).
    - ``"back"``     — jump to the very bottom (behind everything).
    """
    n = len(_get_canvas().elements)
    delta_map = {
        "forward": 1,
        "backward": -1,
        "front": n,
        "back": -n,
    }
    label_map = {
        "forward": "moved forward",
        "backward": "moved backward",
        "front": "brought to front",
        "back": "sent to back",
    }
    delta = delta_map[direction]
    if _get_canvas().move_element(element_id, delta):
        return canvas_png_response(f"'{element_id}' {label_map[direction]}.")
    return canvas_png_response(
        f"'{element_id}' not found or already at the {direction} limit."
    )
