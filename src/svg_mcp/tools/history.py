"""Tool for undoing and redoing canvas changes."""

from __future__ import annotations

from typing import Literal

from fastmcp.utilities.types import ContentBlock

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp


@mcp.tool
def history(action: Literal["undo", "redo"]) -> list[ContentBlock]:
    """Undo or redo canvas changes.

    ``action`` must be one of:
    - ``"undo"`` — revert the last canvas change (up to 50 steps).
    - ``"redo"`` — re-apply the last undone change.
    """
    if action == "undo":
        if _get_canvas().undo():
            return canvas_png_response("Undo successful.")
        return canvas_png_response("Nothing to undo.")
    else:
        if _get_canvas().redo():
            return canvas_png_response("Redo successful.")
        return canvas_png_response("Nothing to redo.")
