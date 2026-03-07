"""Tools for undoing and redoing canvas changes."""

from __future__ import annotations

from mcp import types

import svg_mcp.canvas as _state
from svg_mcp._helpers import canvas_png_response
from svg_mcp.server import mcp


@mcp.tool()
def undo() -> list[types.ContentBlock]:
    """Undo the last canvas change (up to 50 steps)."""
    if _state.canvas.undo():
        return canvas_png_response("Undo successful.")
    return canvas_png_response("Nothing to undo.")


@mcp.tool()
def redo() -> list[types.ContentBlock]:
    """Redo the last undone canvas change."""
    if _state.canvas.redo():
        return canvas_png_response("Redo successful.")
    return canvas_png_response("Nothing to redo.")
