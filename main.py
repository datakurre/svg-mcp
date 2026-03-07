"""SVG MCP Server — draw SVGs on a persistent canvas and export as SVG/PNG."""

from __future__ import annotations

import base64
import html
import os
import uuid
from typing import Any

import cairosvg
from mcp import types
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Canvas state
# ---------------------------------------------------------------------------

_DEFAULT_WIDTH = 800
_DEFAULT_HEIGHT = 600
_DEFAULT_BG = "white"


class Canvas:
    """In-memory SVG canvas that accumulates elements."""

    def __init__(
        self,
        width: int = _DEFAULT_WIDTH,
        height: int = _DEFAULT_HEIGHT,
        background: str = _DEFAULT_BG,
    ):
        self.width = width
        self.height = height
        self.background = background
        self.elements: list[dict[str, Any]] = []  # list of {id, svg_fragment}
        self.defs: list[str] = []  # raw <defs> children

    # -- helpers -------------------------------------------------------------

    def _next_id(self, prefix: str = "el") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def add_element(self, svg_fragment: str, element_id: str | None = None) -> str:
        eid = element_id or self._next_id()
        self.elements.append({"id": eid, "svg": svg_fragment})
        return eid

    def remove_element(self, element_id: str) -> bool:
        before = len(self.elements)
        self.elements = [e for e in self.elements if e["id"] != element_id]
        return len(self.elements) < before

    def clear(self) -> None:
        self.elements.clear()
        self.defs.clear()

    def add_def(self, def_fragment: str) -> None:
        self.defs.append(def_fragment)

    # -- rendering -----------------------------------------------------------

    def to_svg(self) -> str:
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">',
        ]
        if self.defs:
            parts.append("  <defs>")
            for d in self.defs:
                parts.append(f"    {d}")
            parts.append("  </defs>")
        parts.append(
            f'  <rect width="100%" height="100%" fill="{self.background}" />'
        )
        for el in self.elements:
            parts.append(f"  {el['svg']}")
        parts.append("</svg>")
        return "\n".join(parts)

    def to_png_bytes(self, scale: float = 1.0) -> bytes:
        svg_data = self.to_svg()
        return cairosvg.svg2png(
            bytestring=svg_data.encode("utf-8"),
            output_width=int(self.width * scale),
            output_height=int(self.height * scale),
        )

    def to_png_base64(self, scale: float = 1.0) -> str:
        return base64.b64encode(self.to_png_bytes(scale)).decode("ascii")


# Global canvas instance
canvas = Canvas()

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

INSTRUCTIONS = """\
You are an SVG drawing assistant. You have a persistent canvas that you can draw on.

## Workflow
1. Use `create_canvas` to initialise (or reset) the canvas with a desired size and background colour.
2. Add shapes and elements with tools like `draw_rect`, `draw_circle`, `draw_ellipse`, \
`draw_line`, `draw_polyline`, `draw_polygon`, `draw_path`, `draw_text`, `draw_image`, \
and the generic `draw_raw_svg` for anything not covered by a specific tool.
3. Use `add_def` to add reusable definitions (gradients, patterns, clip-paths, …) to the `<defs>` block.
4. Use `list_elements` to see all current element IDs, `remove_element` to delete one, \
or `clear_canvas` to wipe everything.
5. Use `export_svg` or `export_png` to write the current canvas to a file.

Every tool call returns the current canvas rendered as a PNG image so you can visually inspect progress.

## Tips
- All coordinates use the SVG coordinate system (origin top-left, y increases downward).
- Colours accept any CSS colour value (`red`, `#ff0000`, `rgb(255,0,0)`, etc.).
- The `draw_raw_svg` tool accepts *any* valid SVG fragment — use it for advanced shapes or grouped elements.
- You can layer elements; they render in the order they were added.
"""

mcp = FastMCP(
    name="svg-mcp",
    instructions=INSTRUCTIONS,
    log_level="INFO",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _canvas_png_response(message: str = "") -> list[types.ContentBlock]:
    """Return text + current canvas as an embedded PNG image."""
    blocks: list[types.ContentBlock] = []
    if message:
        blocks.append(types.TextContent(type="text", text=message))
    blocks.append(
        types.ImageContent(
            type="image",
            data=canvas.to_png_base64(),
            mimeType="image/png",
        )
    )
    return blocks


def _style_attrs(
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
    opacity: float | None = None,
    extra: dict[str, str] | None = None,
) -> str:
    """Build an attribute string from common style parameters."""
    parts: list[str] = []
    if fill is not None:
        parts.append(f'fill="{fill}"')
    if stroke is not None:
        parts.append(f'stroke="{stroke}"')
    if stroke_width is not None:
        parts.append(f'stroke-width="{stroke_width}"')
    if opacity is not None:
        parts.append(f'opacity="{opacity}"')
    if extra:
        for k, v in extra.items():
            parts.append(f'{k}="{v}"')
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def create_canvas(
    width: int = _DEFAULT_WIDTH,
    height: int = _DEFAULT_HEIGHT,
    background: str = _DEFAULT_BG,
) -> list[types.ContentBlock]:
    """Create or reset the canvas with the given dimensions and background colour."""
    global canvas
    canvas = Canvas(width=width, height=height, background=background)
    return _canvas_png_response(
        f"Canvas created ({width}×{height}, background={background})."
    )


@mcp.tool()
def draw_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    rx: float = 0,
    ry: float = 0,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a rectangle on the canvas."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    transform = f' transform="rotate({rotation} {x + width / 2} {y + height / 2})"' if rotation else ""
    svg = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{rx}" ry="{ry}" {style}{transform} />'
    )
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Rectangle added (id={eid}).")


@mcp.tool()
def draw_circle(
    cx: float,
    cy: float,
    r: float,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a circle on the canvas."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    svg = f'<circle cx="{cx}" cy="{cy}" r="{r}" {style} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Circle added (id={eid}).")


@mcp.tool()
def draw_ellipse(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw an ellipse on the canvas."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    transform = f' transform="rotate({rotation} {cx} {cy})"' if rotation else ""
    svg = f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {style}{transform} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Ellipse added (id={eid}).")


@mcp.tool()
def draw_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    stroke_linecap: str = "round",
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a straight line on the canvas."""
    style = _style_attrs(stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    svg = (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'{style} stroke-linecap="{stroke_linecap}" />'
    )
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Line added (id={eid}).")


@mcp.tool()
def draw_polyline(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a polyline (open shape). `points` is a space-separated list like '0,0 50,50 100,0'."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    svg = f'<polyline points="{points}" {style} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Polyline added (id={eid}).")


@mcp.tool()
def draw_polygon(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a polygon (closed shape). `points` is a space-separated list like '100,10 40,198 190,78 10,78 160,198'."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    svg = f'<polygon points="{points}" {style} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Polygon added (id={eid}).")


@mcp.tool()
def draw_path(
    d: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw an SVG path. `d` is the path data string (e.g. 'M10 80 C 40 10, 65 10, 95 80 S 150 150, 180 80')."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity)
    svg = f'<path d="{d}" {style} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Path added (id={eid}).")


@mcp.tool()
def draw_text(
    x: float,
    y: float,
    text: str,
    font_size: float = 16,
    font_family: str = "sans-serif",
    fill: str = "black",
    text_anchor: str = "start",
    font_weight: str = "normal",
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw text on the canvas."""
    style = _style_attrs(
        fill=fill,
        opacity=opacity,
        extra={
            "font-size": str(font_size),
            "font-family": font_family,
            "text-anchor": text_anchor,
            "font-weight": font_weight,
        },
    )
    transform = f' transform="rotate({rotation} {x} {y})"' if rotation else ""
    safe_text = html.escape(text)
    svg = f'<text x="{x}" y="{y}" {style}{transform}>{safe_text}</text>'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Text added (id={eid}).")


@mcp.tool()
def draw_image(
    x: float,
    y: float,
    width: float,
    height: float,
    href: str,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Embed an external image (URL or data-URI) on the canvas."""
    style = _style_attrs(opacity=opacity)
    svg = (
        f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
        f'href="{href}" {style} />'
    )
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Image added (id={eid}).")


@mcp.tool()
def draw_raw_svg(
    svg_fragment: str,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Add an arbitrary SVG fragment to the canvas. Use for groups (<g>), filters, clip-paths, or anything not covered by the other draw tools."""
    eid = canvas.add_element(svg_fragment, element_id)
    return _canvas_png_response(f"Raw SVG element added (id={eid}).")


@mcp.tool()
def add_def(
    def_fragment: str,
) -> list[types.ContentBlock]:
    """Add a definition (gradient, pattern, clip-path, filter, etc.) to the <defs> section.

    Example: '<linearGradient id="grad1"><stop offset="0%" stop-color="red"/><stop offset="100%" stop-color="blue"/></linearGradient>'
    """
    canvas.add_def(def_fragment)
    return _canvas_png_response("Definition added to <defs>.")


@mcp.tool()
def list_elements() -> list[types.ContentBlock]:
    """List all element IDs currently on the canvas."""
    if not canvas.elements:
        return _canvas_png_response("Canvas is empty — no elements.")
    lines = [f"- {e['id']}" for e in canvas.elements]
    return _canvas_png_response("Elements on canvas:\n" + "\n".join(lines))


@mcp.tool()
def remove_element(element_id: str) -> list[types.ContentBlock]:
    """Remove an element from the canvas by its ID."""
    if canvas.remove_element(element_id):
        return _canvas_png_response(f"Element '{element_id}' removed.")
    return _canvas_png_response(f"Element '{element_id}' not found.")


@mcp.tool()
def clear_canvas() -> list[types.ContentBlock]:
    """Remove all elements (and defs) from the canvas, keeping its size and background."""
    canvas.clear()
    return _canvas_png_response("Canvas cleared.")


@mcp.tool()
def get_canvas() -> list[types.ContentBlock]:
    """Return the current canvas as a PNG preview (no changes)."""
    return _canvas_png_response(
        f"Canvas: {canvas.width}×{canvas.height}, "
        f"background={canvas.background}, "
        f"{len(canvas.elements)} element(s)."
    )


@mcp.tool()
def get_svg_source() -> list[types.ContentBlock]:
    """Return the raw SVG source of the current canvas."""
    svg = canvas.to_svg()
    return _canvas_png_response(f"```xml\n{svg}\n```")


@mcp.tool()
def export_svg(file_path: str) -> list[types.ContentBlock]:
    """Export the current canvas to an SVG file."""
    path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(canvas.to_svg())
    return _canvas_png_response(f"SVG exported to `{path}`.")


@mcp.tool()
def export_png(file_path: str, scale: float = 1.0) -> list[types.ContentBlock]:
    """Export the current canvas to a PNG file. `scale` multiplies the output resolution (e.g. 2.0 for retina)."""
    path = os.path.abspath(file_path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(canvas.to_png_bytes(scale=scale))
    return _canvas_png_response(f"PNG exported to `{path}` (scale={scale}).")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
