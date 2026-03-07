"""svg_mcp — SVG MCP server package."""

from svg_mcp import tools as _tools  # noqa: F401 — registers all tools
from svg_mcp.canvas import canvas
from svg_mcp.server import mcp

__all__ = ["mcp", "canvas"]
