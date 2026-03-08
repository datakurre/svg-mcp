"""Tools for adding, inspecting, updating, removing elements and defs."""

from __future__ import annotations

import json
import re as _re

import drawsvg as _draw
from fastmcp.utilities.types import Image

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp

_DEFS_PAT = _re.compile(r"<defs>(.*?)</defs>", _re.DOTALL)


def _def_elem_to_svg(def_elem) -> str:
    """Extract the inner SVG fragment of a drawsvg def element."""
    tmp = _draw.Drawing(1, 1)
    tmp.append_def(def_elem)
    raw = tmp.as_svg()
    m = _DEFS_PAT.search(raw)
    if m:
        return m.group(1).strip()
    return ""


def _build_def_from_kind(kind: str, def_id: str, params: dict) -> str:
    """Build an SVG def fragment using drawsvg typed classes.

    Supported kinds and their ``params`` keys:

    ``"linear_gradient"``
        ``x1, y1, x2, y2`` (0–1 fractions; default objectBoundingBox),
        ``gradient_units`` ("objectBoundingBox" or "userSpaceOnUse"),
        ``stops`` — list of ``{"offset": float|str, "color": str, "opacity": float}``.

    ``"radial_gradient"``
        ``cx, cy, r`` (fractions), ``gradient_units``, ``stops``.

    ``"pattern"``
        ``x, y, width, height``, ``pattern_units`` ("userSpaceOnUse" or
        "objectBoundingBox"), ``content`` — raw SVG string of child elements.

    ``"clip_path"``
        ``content`` — raw SVG string of clipping shapes.

    ``"marker"``
        ``min_x, min_y, width, height`` (viewBox corners and size),
        ``scale``, ``orient`` ("auto" or angle),
        ``content`` — raw SVG string of marker shapes.
    """
    if kind == "linear_gradient":
        x1 = params.get("x1", 0)
        y1 = params.get("y1", 0)
        x2 = params.get("x2", 1)
        y2 = params.get("y2", 0)
        gu = params.get("gradient_units", "objectBoundingBox")
        elem = _draw.LinearGradient(x1, y1, x2, y2, gradientUnits=gu, id=def_id)
        for stop in params.get("stops", []):
            elem.add_stop(stop["offset"], stop["color"], stop.get("opacity", 1))
        return _def_elem_to_svg(elem)

    if kind == "radial_gradient":
        cx = params.get("cx", 0.5)
        cy = params.get("cy", 0.5)
        r = params.get("r", 0.5)
        gu = params.get("gradient_units", "objectBoundingBox")
        elem = _draw.RadialGradient(cx, cy, r, gradientUnits=gu, id=def_id)
        for stop in params.get("stops", []):
            elem.add_stop(stop["offset"], stop["color"], stop.get("opacity", 1))
        return _def_elem_to_svg(elem)

    if kind == "pattern":
        x = params.get("x", 0)
        y = params.get("y", 0)
        w = params.get("width", 10)
        h = params.get("height", 10)
        pu = params.get("pattern_units", "userSpaceOnUse")
        content = params.get("content", "")
        pat = _draw.Pattern(x, y, w, h, patternUnits=pu, id=def_id)
        if content:
            pat.append(_draw.Raw(content))
        return _def_elem_to_svg(pat)

    if kind == "clip_path":
        content = params.get("content", "")
        cp = _draw.ClipPath(id=def_id)
        if content:
            cp.append(_draw.Raw(content))
        return _def_elem_to_svg(cp)

    if kind == "marker":
        min_x = params.get("min_x", -0.1)
        min_y = params.get("min_y", -0.5)
        width = params.get("width", 1.0)
        height = params.get("height", 1.0)
        scale = params.get("scale", 4)
        orient = params.get("orient", "auto")
        content = params.get("content", "")
        m = _draw.Marker(
            min_x,
            min_y,
            min_x + width,
            min_y + height,
            scale=scale,
            orient=orient,
            id=def_id,
        )
        if content:
            m.append(_draw.Raw(content))
        return _def_elem_to_svg(m)

    raise ValueError(
        f"Unknown kind '{kind}'. Must be one of: linear_gradient, radial_gradient, "
        "pattern, clip_path, marker."
    )


@mcp.tool
def update_element(
    element_id: str,
    svg_fragment: str,
) -> list[str | Image]:
    """Replace the SVG fragment of an existing element in-place, identified by its ID.

    Use ``inspect(what='element', element_id=...)`` first to fetch the current fragment,
    edit it, then call this tool.  The element stays at the same z-position in the stack.
    """
    if _get_canvas().update_element(element_id, svg_fragment):
        return canvas_png_response(f"Element '{element_id}' updated.")
    return canvas_png_response(f"Element '{element_id}' not found — no changes made.")


@mcp.tool
def remove_element(element_id: str) -> list[str | Image]:
    """Remove an element from the canvas by its ID."""
    if _get_canvas().remove_element(element_id):
        return canvas_png_response(f"Element '{element_id}' removed.")
    return canvas_png_response(f"Element '{element_id}' not found.")


@mcp.tool
def add_def(
    def_fragment: str = "",
    kind: str = "",
    def_id: str = "",
    params: str = "",
) -> list[str | Image]:
    """Add a definition (gradient, pattern, clip-path, filter, etc.) to the <defs> section.

    **Raw SVG mode** (default) — pass any SVG def fragment as ``def_fragment``:

        def_fragment='<linearGradient id="g1">...'

    **Typed mode** — pass ``kind``, ``def_id``, and ``params`` (JSON object string)
    to have the def built automatically by drawsvg without writing raw XML.

    Supported ``kind`` values and their ``params`` keys:

    ``"linear_gradient"``
        ``x1, y1, x2, y2`` (0–1 fractions, objectBoundingBox by default),
        ``gradient_units``, ``stops`` — list of ``{"offset", "color", "opacity"}``.

    ``"radial_gradient"``
        ``cx, cy, r`` (fractions), ``gradient_units``, ``stops``.

    ``"pattern"``
        ``x, y, width, height``, ``pattern_units``,
        ``content`` — raw SVG child elements string.

    ``"clip_path"``
        ``content`` — raw SVG clipping-shape string.

    ``"marker"``
        ``min_x, min_y, width, height``, ``scale``, ``orient``,
        ``content`` — raw SVG marker-shape string.

    Example — create a red→blue horizontal linear gradient::

        kind="linear_gradient", def_id="grad1",
        params='{"x1":0,"y1":0,"x2":1,"y2":0,"stops":[{"offset":0,"color":"red"},{"offset":1,"color":"blue"}]}'
    """
    if kind:
        parsed_params: dict = json.loads(params) if params else {}
        fragment = _build_def_from_kind(kind, def_id, parsed_params)
    else:
        fragment = def_fragment

    _get_canvas().add_def(fragment)
    return canvas_png_response("Definition added to <defs>.")
