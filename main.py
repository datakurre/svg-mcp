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


# Maximum number of undo snapshots kept in memory
_MAX_HISTORY = 50


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
        self._history: list[dict[str, Any]] = []  # undo stack
        self._future: list[dict[str, Any]] = []   # redo stack

    # -- helpers -------------------------------------------------------------

    def _next_id(self, prefix: str = "el") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def _snapshot(self) -> dict[str, Any]:
        """Return a deep snapshot of mutable state."""
        import copy
        return {
            "elements": copy.deepcopy(self.elements),
            "defs": list(self.defs),
        }

    def _push_history(self) -> None:
        """Save current state to undo stack and clear redo stack."""
        self._history.append(self._snapshot())
        if len(self._history) > _MAX_HISTORY:
            self._history.pop(0)
        self._future.clear()

    def _restore(self, snapshot: dict[str, Any]) -> None:
        self.elements = snapshot["elements"]
        self.defs = snapshot["defs"]

    def undo(self) -> bool:
        if not self._history:
            return False
        self._future.append(self._snapshot())
        self._restore(self._history.pop())
        return True

    def redo(self) -> bool:
        if not self._future:
            return False
        self._history.append(self._snapshot())
        self._restore(self._future.pop())
        return True

    def add_element(self, svg_fragment: str, element_id: str | None = None) -> str:
        self._push_history()
        eid = element_id or self._next_id()
        self.elements.append({"id": eid, "svg": svg_fragment})
        return eid

    def update_element(self, element_id: str, svg_fragment: str) -> bool:
        """Replace the SVG fragment of an existing element in-place."""
        for el in self.elements:
            if el["id"] == element_id:
                self._push_history()
                el["svg"] = svg_fragment
                return True
        return False

    def remove_element(self, element_id: str) -> bool:
        before = len(self.elements)
        if before == len([e for e in self.elements if e["id"] != element_id]):
            return False
        self._push_history()
        self.elements = [e for e in self.elements if e["id"] != element_id]
        return True

    def get_element_svg(self, element_id: str) -> str | None:
        """Return the raw SVG fragment for a single element, or None."""
        for el in self.elements:
            if el["id"] == element_id:
                return el["svg"]
        return None

    def move_element(self, element_id: str, delta: int) -> bool:
        """Move element up (delta>0) or down (delta<0) in the z-order."""
        idx = next((i for i, e in enumerate(self.elements) if e["id"] == element_id), None)
        if idx is None:
            return False
        new_idx = max(0, min(len(self.elements) - 1, idx + delta))
        if new_idx == idx:
            return False
        self._push_history()
        el = self.elements.pop(idx)
        self.elements.insert(new_idx, el)
        return True

    def clear(self) -> None:
        self._push_history()
        self.elements.clear()
        self.defs.clear()

    def resize(self, width: int, height: int, background: str | None = None) -> None:
        """Change canvas dimensions (and optionally background) without clearing elements."""
        self._push_history()
        self.width = width
        self.height = height
        if background is not None:
            self.background = background

    def add_def(self, def_fragment: str) -> None:
        self._push_history()
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
   Use `resize_canvas` to change dimensions without losing elements.
2. Add shapes and elements with tools like `draw_rect`, `draw_circle`, `draw_ellipse`,
   `draw_line`, `draw_polyline`, `draw_polygon`, `draw_path`, `draw_text`, `draw_image`,
   `draw_group` (for grouped/transformed sets of shapes), and the generic `draw_raw_svg`.
3. Use `add_def` to add reusable definitions (gradients, patterns, clip-paths, …) to the `<defs>` block.
4. Inspect with `list_elements` and `get_element` (shows a single element's SVG source).
5. Edit in place with `update_element` — replace any element's SVG without removing it.
6. Reorder with `bring_forward` / `send_backward` / `bring_to_front` / `send_to_back`.
7. Undo mistakes with `undo`, re-apply with `redo` (up to 50 steps).
8. Remove one element with `remove_element`, or wipe everything with `clear_canvas`.
9. Export with `export_svg` or `export_png`.

Every tool call returns the current canvas rendered as a PNG image so you can visually inspect progress.

## Tips
- All coordinates use the SVG coordinate system (origin top-left, y increases downward).
- Colours accept any CSS colour value (`red`, `#ff0000`, `rgb(255,0,0)`, etc.).
- All draw tools accept `stroke_dasharray` (e.g. `"5,3"`) for dashed lines.
- `draw_group` wraps children in `<g transform="...">` — great for translate/rotate/scale sets.
- `draw_raw_svg` accepts *any* valid SVG fragment as a last resort.
- Elements render in the order they were added; use reorder tools to change depth.
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
    stroke_dasharray: str | None = None,
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
    if stroke_dasharray is not None:
        parts.append(f'stroke-dasharray="{stroke_dasharray}"')
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
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a rectangle on the canvas."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
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
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a circle on the canvas."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
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
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw an ellipse on the canvas."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
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
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    stroke_linecap: str = "round",
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a straight line on the canvas."""
    style = _style_attrs(stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
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
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a polyline (open shape). `points` is a space-separated list like '0,0 50,50 100,0'."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
    svg = f'<polyline points="{points}" {style} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Polyline added (id={eid}).")


@mcp.tool()
def draw_polygon(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw a polygon (closed shape). `points` is a space-separated list like '100,10 40,198 190,78 10,78 160,198'."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
    svg = f'<polygon points="{points}" {style} />'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Polygon added (id={eid}).")


@mcp.tool()
def draw_path(
    d: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Draw an SVG path. `d` is the path data string (e.g. 'M10 80 C 40 10, 65 10, 95 80 S 150 150, 180 80')."""
    style = _style_attrs(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, stroke_dasharray=stroke_dasharray)
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
def resize_canvas(
    width: int,
    height: int,
    background: str | None = None,
) -> list[types.ContentBlock]:
    """Resize the canvas without clearing its elements. Optionally change the background colour."""
    canvas.resize(width, height, background)
    return _canvas_png_response(
        f"Canvas resized to {width}×{height}"
        + (f", background={background}" if background else "") + "."
    )


@mcp.tool()
def update_element(
    element_id: str,
    svg_fragment: str,
) -> list[types.ContentBlock]:
    """Replace the SVG fragment of an existing element in-place, identified by its ID.

    Use `get_element` first to fetch the current fragment, edit it, then call this tool.
    The element stays at the same z-position in the stack.
    """
    if canvas.update_element(element_id, svg_fragment):
        return _canvas_png_response(f"Element '{element_id}' updated.")
    return _canvas_png_response(f"Element '{element_id}' not found — no changes made.")


@mcp.tool()
def get_element(element_id: str) -> list[types.ContentBlock]:
    """Return the raw SVG fragment for a single element on the canvas."""
    svg = canvas.get_element_svg(element_id)
    if svg is None:
        return _canvas_png_response(f"Element '{element_id}' not found.")
    return _canvas_png_response(f"Element '{element_id}':\n```xml\n{svg}\n```")


@mcp.tool()
def draw_group(
    children: str,
    transform: str = "",
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Wrap one or more SVG fragments in a `<g>` group element.

    `children` — raw SVG fragments concatenated as a single string, e.g.
        '<circle cx="50" cy="50" r="40" fill="red"/><text x="50" y="55" text-anchor="middle">Hi</text>'

    `transform` — any SVG transform string, e.g. 'translate(100,50) rotate(45)'

    Groups are useful for:
    - Applying a shared transform to multiple shapes at once
    - Applying shared opacity to a set of overlapping elements
    - Organising related shapes so they can be updated or removed together
    """
    attrs = []
    if transform:
        attrs.append(f'transform="{transform}"')
    if opacity != 1.0:
        attrs.append(f'opacity="{opacity}"')
    attr_str = " ".join(attrs)
    svg = f'<g {attr_str}>{children}</g>' if attr_str else f'<g>{children}</g>'
    eid = canvas.add_element(svg, element_id)
    return _canvas_png_response(f"Group added (id={eid}).")


@mcp.tool()
def undo() -> list[types.ContentBlock]:
    """Undo the last canvas change (up to 50 steps)."""
    if canvas.undo():
        return _canvas_png_response("Undo successful.")
    return _canvas_png_response("Nothing to undo.")


@mcp.tool()
def redo() -> list[types.ContentBlock]:
    """Redo the last undone canvas change."""
    if canvas.redo():
        return _canvas_png_response("Redo successful.")
    return _canvas_png_response("Nothing to redo.")


@mcp.tool()
def bring_forward(element_id: str) -> list[types.ContentBlock]:
    """Move an element one step forward (higher in the z-order, rendered later = on top)."""
    if canvas.move_element(element_id, +1):
        return _canvas_png_response(f"'{element_id}' moved forward.")
    return _canvas_png_response(f"'{element_id}' not found or already at the top.")


@mcp.tool()
def send_backward(element_id: str) -> list[types.ContentBlock]:
    """Move an element one step backward (lower in the z-order, rendered earlier = behind)."""
    if canvas.move_element(element_id, -1):
        return _canvas_png_response(f"'{element_id}' moved backward.")
    return _canvas_png_response(f"'{element_id}' not found or already at the bottom.")


@mcp.tool()
def bring_to_front(element_id: str) -> list[types.ContentBlock]:
    """Move an element to the very top of the z-order (rendered last = in front of everything)."""
    n = len(canvas.elements)
    if canvas.move_element(element_id, n):
        return _canvas_png_response(f"'{element_id}' brought to front.")
    return _canvas_png_response(f"'{element_id}' not found or already at the front.")


@mcp.tool()
def send_to_back(element_id: str) -> list[types.ContentBlock]:
    """Move an element to the very bottom of the z-order (rendered first = behind everything)."""
    n = len(canvas.elements)
    if canvas.move_element(element_id, -n):
        return _canvas_png_response(f"'{element_id}' sent to back.")
    return _canvas_png_response(f"'{element_id}' not found or already at the back.")


@mcp.tool()
def list_elements() -> list[types.ContentBlock]:
    """List all element IDs currently on the canvas (in z-order, bottom to top)."""
    if not canvas.elements:
        return _canvas_png_response("Canvas is empty — no elements.")
    lines = [f"{i + 1}. {e['id']}" for i, e in enumerate(canvas.elements)]
    return _canvas_png_response("Elements on canvas (bottom → top):\n" + "\n".join(lines))


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
