"""Tools for drawing shapes, text, images, and groups onto the canvas."""

from __future__ import annotations

import html as _html

from mcp import types

from svg_mcp._helpers import canvas_png_response, style_attrs
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp


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
    style = style_attrs(
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    transform = (
        f' transform="rotate({rotation} {x + width / 2} {y + height / 2})"'
        if rotation else ""
    )
    svg = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{rx}" ry="{ry}" {style}{transform} />'
    )
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
    style = style_attrs(
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    svg = f'<circle cx="{cx}" cy="{cy}" r="{r}" {style} />'
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
    style = style_attrs(
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    transform = f' transform="rotate({rotation} {cx} {cy})"' if rotation else ""
    svg = f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {style}{transform} />'
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
    style = style_attrs(
        stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    svg = (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'{style} stroke-linecap="{stroke_linecap}" />'
    )
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
    style = style_attrs(
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    svg = f'<polyline points="{points}" {style} />'
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
    style = style_attrs(
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    svg = f'<polygon points="{points}" {style} />'
    return _get_canvas().add_element(svg, element_id)


def _draw_path(
    d: str,
    fill: str = "none",
    stroke: str = "black",
    stroke_width: float = 1,
    stroke_dasharray: str | None = None,
    opacity: float = 1.0,
    element_id: str | None = None,
) -> str:
    style = style_attrs(
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        opacity=opacity, stroke_dasharray=stroke_dasharray,
    )
    svg = f'<path d="{d}" {style} />'
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
    style = style_attrs(
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
    svg = f'<text x="{x}" y="{y}" {style}{transform}>{_html.escape(text)}</text>'
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
    style = style_attrs(opacity=opacity)
    svg = (
        f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
        f'href="{href}" {style} />'
    )
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
    svg = f'<g {attr_str}>{children}</g>' if attr_str else f'<g>{children}</g>'
    return _get_canvas().add_element(svg, element_id)


def _draw_raw_svg(
    svg_fragment: str,
    element_id: str | None = None,
) -> str:
    return _get_canvas().add_element(svg_fragment, element_id)


# ---------------------------------------------------------------------------
# MCP tool wrappers
# ---------------------------------------------------------------------------

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
    eid = _draw_rect(
        x=x, y=y, width=width, height=height, rx=rx, ry=ry,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        rotation=rotation, element_id=element_id,
    )
    return canvas_png_response(f"Rectangle added (id={eid}).")


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
    eid = _draw_circle(
        cx=cx, cy=cy, r=r,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        element_id=element_id,
    )
    return canvas_png_response(f"Circle added (id={eid}).")


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
    eid = _draw_ellipse(
        cx=cx, cy=cy, rx=rx, ry=ry,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        rotation=rotation, element_id=element_id,
    )
    return canvas_png_response(f"Ellipse added (id={eid}).")


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
    eid = _draw_line(
        x1=x1, y1=y1, x2=x2, y2=y2,
        stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        stroke_linecap=stroke_linecap, element_id=element_id,
    )
    return canvas_png_response(f"Line added (id={eid}).")


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
    eid = _draw_polyline(
        points=points,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        element_id=element_id,
    )
    return canvas_png_response(f"Polyline added (id={eid}).")


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
    eid = _draw_polygon(
        points=points,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        element_id=element_id,
    )
    return canvas_png_response(f"Polygon added (id={eid}).")


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
    eid = _draw_path(
        d=d,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
        stroke_dasharray=stroke_dasharray, opacity=opacity,
        element_id=element_id,
    )
    return canvas_png_response(f"Path added (id={eid}).")


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
    eid = _draw_text(
        x=x, y=y, text=text,
        font_size=font_size, font_family=font_family,
        fill=fill, text_anchor=text_anchor, font_weight=font_weight,
        opacity=opacity, rotation=rotation, element_id=element_id,
    )
    return canvas_png_response(f"Text added (id={eid}).")


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
    eid = _draw_image(
        x=x, y=y, width=width, height=height, href=href,
        opacity=opacity, element_id=element_id,
    )
    return canvas_png_response(f"Image added (id={eid}).")


@mcp.tool()
def draw_group(
    children: str,
    transform: str = "",
    opacity: float = 1.0,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
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
        children=children, transform=transform, opacity=opacity,
        element_id=element_id,
    )
    return canvas_png_response(f"Group added (id={eid}).")


@mcp.tool()
def draw_raw_svg(
    svg_fragment: str,
    element_id: str | None = None,
) -> list[types.ContentBlock]:
    """Add an arbitrary SVG fragment to the canvas.

    Use for `<use>`, `<symbol>`, filters, or anything not covered by the other draw tools.
    """
    eid = _draw_raw_svg(svg_fragment=svg_fragment, element_id=element_id)
    return canvas_png_response(f"Raw SVG element added (id={eid}).")
