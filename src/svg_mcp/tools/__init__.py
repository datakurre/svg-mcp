"""Register all tool modules by importing them (side-effect: decorators run)."""

from svg_mcp.tools import batch, canvas_mgmt, drawing, elements, history, zorder

__all__ = ["batch", "canvas_mgmt", "drawing", "elements", "history", "zorder"]
