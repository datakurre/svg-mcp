"""Tools for drawing shapes, text, images, and groups onto the canvas."""

from __future__ import annotations

import re as _re

import drawsvg as _draw
from fastmcp.utilities.types import Image

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp

# ---------------------------------------------------------------------------
# Private helper: serialise a drawsvg element to an SVG fragment string.
# We render it via a minimal temporary Drawing then strip the wrapper.
# ---------------------------------------------------------------------------

_DEFS_PAT = _re.compile(r"<defs>.*?</defs>", _re.DOTALL)


def _elem_svg(elem: _draw.DrawingElement) -> str:
    """Return the SVG fragment string for a single drawsvg element."""
    tmp = _draw.Drawing(1, 1)
    tmp.append(elem)
    raw = tmp.as_svg()
    # Strip XML declaration, SVG opening/closing tags, and empty defs block.
    body = _re.sub(r"<\?xml[^?]*\?>", "", raw)
    body = _re.sub(r"<svg[^>]*>", "", body)
    body = _re.sub(r"</svg>", "", body)
    body = _DEFS_PAT.sub("", body)
    return body.strip()


# ---------------------------------------------------------------------------
# Pure core functions (no MCP dependency – usable from batch and tools alike)
# ---------------------------------------------------------------------------


def _draw_rect(
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
) -> str:
    kwargs: dict = dict(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    if rotation:
        cx = x + width / 2
        cy = y + height / 2
        kwargs["transform"] = f"rotate({rotation} {cx} {cy})"
    elem = _draw.Rectangle(x, y, width, height, rx=rx, ry=ry, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_circle(
    cx: float,
    cy: float,
    r: float,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> str:
    kwargs: dict = dict(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    elem = _draw.Circle(cx, cy, r, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_ellipse(
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
) -> str:
    kwargs: dict = dict(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    if rotation:
        kwargs["transform"] = f"rotate({rotation} {cx} {cy})"
    elem = _draw.Ellipse(cx, cy, rx, ry, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_line(
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
) -> str:
    kwargs: dict = dict(
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
        stroke_linecap=stroke_linecap,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    elem = _draw.Line(x1, y1, x2, y2, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_polyline(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> str:
    # Parse "x,y x,y …" into flat coordinate list for drawsvg.Lines.
    coords: list[float] = []
    for pair in points.strip().split():
        x_s, y_s = pair.split(",")
        coords.extend([float(x_s), float(y_s)])
    kwargs: dict = dict(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
        close=False,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    elem = _draw.Lines(*coords, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_polygon(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> str:
    # Parse "x,y x,y …" into flat coordinate list for drawsvg.Lines.
    coords: list[float] = []
    for pair in points.strip().split():
        x_s, y_s = pair.split(",")
        coords.extend([float(x_s), float(y_s)])
    kwargs: dict = dict(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
        close=True,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    elem = _draw.Lines(*coords, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_path(
    d: str = "",
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
    # Arc convenience params — when provided, d is ignored.
    arc_cx: float | None = None,
    arc_cy: float | None = None,
    arc_r: float | None = None,
    arc_start_deg: float | None = None,
    arc_end_deg: float | None = None,
    arc_cw: bool = False,
) -> str:
    kwargs: dict = dict(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray

    arc_params = (arc_cx, arc_cy, arc_r, arc_start_deg, arc_end_deg)
    if any(p is not None for p in arc_params):
        # Validate that all arc params are supplied together.
        if not all(p is not None for p in arc_params):
            raise ValueError(
                "All arc params (arc_cx, arc_cy, arc_r, arc_start_deg, arc_end_deg) "
                "must be provided together."
            )
        if d and d.strip():
            raise ValueError(
                "Provide either a raw `d` path string or arc params, not both."
            )
        elem = _draw.Arc(
            arc_cx,
            arc_cy,
            arc_r,
            arc_start_deg,
            arc_end_deg,  # type: ignore[arg-type]
            cw=arc_cw,
            **kwargs,
        )
    else:
        elem = _draw.Path(d=d, **kwargs)

    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_text(
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
) -> str:
    kwargs: dict = dict(
        fill=fill,
        opacity=opacity,
        text_anchor=text_anchor,
        font_family=font_family,
        font_weight=font_weight,
    )
    if rotation:
        kwargs["transform"] = f"rotate({rotation} {x} {y})"
    # Pass raw text — drawsvg HTML-escapes content automatically.
    elem = _draw.Text(text, font_size, x, y, **kwargs)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_image(
    x: float,
    y: float,
    width: float,
    height: float,
    href: str,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> str:
    elem = _draw.Image(x, y, width, height, path=href, opacity=opacity)
    svg = _elem_svg(elem)
    return _get_canvas().add_element(svg, element_id)


def _draw_group(
    children: str,
    transform: str = "",
    opacity: float = 1.0,
    element_id: str | None = None,
) -> str:
    attrs: list[str] = []
    if transform:
        attrs.append(f'transform="{transform}"')
    if opacity != 1.0:
        attrs.append(f'opacity="{opacity}"')
    attr_str = " ".join(attrs)
    svg = f"<g {attr_str}>{children}</g>" if attr_str else f"<g>{children}</g>"
    return _get_canvas().add_element(svg, element_id)


def _draw_raw_svg(
    svg_fragment: str,
    element_id: str | None = None,
) -> str:
    return _get_canvas().add_element(svg_fragment, element_id)


# ---------------------------------------------------------------------------
# MCP tool wrappers
# ---------------------------------------------------------------------------


@mcp.tool
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
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str = "",
) -> list[str | Image]:
    """Draw a rectangle on the canvas."""
    eid = _draw_rect(
        x=x,
        y=y,
        width=width,
        height=height,
        rx=rx,
        ry=ry,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        rotation=rotation,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Rectangle added (id={eid}).")


@mcp.tool
def draw_circle(
    cx: float,
    cy: float,
    r: float,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    element_id: str = "",
) -> list[str | Image]:
    """Draw a circle on the canvas."""
    eid = _draw_circle(
        cx=cx,
        cy=cy,
        r=r,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Circle added (id={eid}).")


@mcp.tool
def draw_ellipse(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    rotation: float = 0,
    element_id: str = "",
) -> list[str | Image]:
    """Draw an ellipse on the canvas."""
    eid = _draw_ellipse(
        cx=cx,
        cy=cy,
        rx=rx,
        ry=ry,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        rotation=rotation,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Ellipse added (id={eid}).")


@mcp.tool
def draw_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    stroke_linecap: str = "round",
    element_id: str = "",
) -> list[str | Image]:
    """Draw a straight line on the canvas."""
    eid = _draw_line(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        stroke_linecap=stroke_linecap,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Line added (id={eid}).")


@mcp.tool
def draw_polyline(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    element_id: str = "",
) -> list[str | Image]:
    """Draw a polyline (open shape). `points` is a space-separated list like '0,0 50,50 100,0'."""
    eid = _draw_polyline(
        points=points,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Polyline added (id={eid}).")


@mcp.tool
def draw_polygon(
    points: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    element_id: str = "",
) -> list[str | Image]:
    """Draw a polygon (closed shape). `points` is a space-separated list like '100,10 40,198 190,78 10,78 160,198'."""
    eid = _draw_polygon(
        points=points,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Polygon added (id={eid}).")


@mcp.tool
def draw_path(
    d: str = "",
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str = "",
    opacity: float = 1.0,
    element_id: str = "",
    arc_cx: float = 0,
    arc_cy: float = 0,
    arc_r: float = 0,
    arc_start_deg: float = 0,
    arc_end_deg: float = 0,
    arc_cw: bool = False,
) -> list[str | Image]:
    """Draw an SVG path. `d` is the path data string (e.g. 'M10 80 C 40 10, 65 10, 95 80 S 150 150, 180 80').

    Alternatively, supply arc convenience params to draw a circular arc without doing
    trigonometry manually.  When any arc param is non-zero the `d` argument is ignored.

    Arc params:
    - ``arc_cx``, ``arc_cy`` — centre of the circle.
    - ``arc_r``              — radius.
    - ``arc_start_deg``      — start angle in degrees (0 = right, 90 = down).
    - ``arc_end_deg``        — end angle in degrees.
    - ``arc_cw``             — draw clockwise when True (default False = counter-clockwise).
    """
    # Detect whether the caller wants arc mode.
    use_arc = arc_r != 0 or arc_start_deg != 0 or arc_end_deg != 0
    eid = _draw_path(
        d=d,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray or None,
        opacity=opacity,
        element_id=element_id or None,
        arc_cx=arc_cx if use_arc else None,
        arc_cy=arc_cy if use_arc else None,
        arc_r=arc_r if use_arc else None,
        arc_start_deg=arc_start_deg if use_arc else None,
        arc_end_deg=arc_end_deg if use_arc else None,
        arc_cw=arc_cw,
    )
    return canvas_png_response(f"Path added (id={eid}).")


@mcp.tool
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
    element_id: str = "",
) -> list[str | Image]:
    """Draw text on the canvas."""
    eid = _draw_text(
        x=x,
        y=y,
        text=text,
        font_size=font_size,
        font_family=font_family,
        fill=fill,
        text_anchor=text_anchor,
        font_weight=font_weight,
        opacity=opacity,
        rotation=rotation,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Text added (id={eid}).")


@mcp.tool
def draw_image(
    x: float,
    y: float,
    width: float,
    height: float,
    href: str,
    opacity: float = 1.0,
    element_id: str = "",
) -> list[str | Image]:
    """Embed an external image (URL or data-URI) on the canvas."""
    eid = _draw_image(
        x=x,
        y=y,
        width=width,
        height=height,
        href=href,
        opacity=opacity,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Image added (id={eid}).")


@mcp.tool
def draw_group(
    children: str,
    transform: str = "",
    opacity: float = 1.0,
    element_id: str = "",
) -> list[str | Image]:
    """Wrap one or more SVG fragments in a `<g>` group element.

    `children` — raw SVG fragments concatenated as a single string, e.g.
        '<circle cx="50" cy="50" r="40" fill="red"/>'
        '<text x="50" y="55" text-anchor="middle">Hi</text>'

    `transform` — any SVG transform string, e.g. 'translate(100,50) rotate(45)'

    Groups are useful for:
    - Applying a shared transform or opacity to multiple shapes at once
    - Organising related shapes so they can be updated or removed together
    """
    eid = _draw_group(
        children=children,
        transform=transform,
        opacity=opacity,
        element_id=element_id or None,
    )
    return canvas_png_response(f"Group added (id={eid}).")


@mcp.tool
def draw_raw_svg(
    svg_fragment: str,
    element_id: str = "",
) -> list[str | Image]:
    """Add an arbitrary SVG fragment to the canvas.

    Use for `<use>`, `<symbol>`, filters, or anything not covered by the other draw tools.
    """
    eid = _draw_raw_svg(svg_fragment=svg_fragment, element_id=element_id or None)
    return canvas_png_response(f"Raw SVG element added (id={eid}).")
