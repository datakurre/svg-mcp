"""Entry point — delegates entirely to the svg_mcp package."""

from svg_mcp import mcp  # noqa: F401 — imports register all tools

if __name__ == "__main__":
    mcp.run(transport="stdio")
