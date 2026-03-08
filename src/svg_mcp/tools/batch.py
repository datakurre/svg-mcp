"""Batch tool — execute multiple draw/element operations in a single call."""

from __future__ import annotations

from typing import Any

from mcp import types

from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import Canvas, get_canvas as _get_canvas, set_canvas
from svg_mcp.server import mcp

# ---------------------------------------------------------------------------
# Dispatch table: maps tool name → callable that accepts **kwargs and returns
# a short string describing what happened (used to build the summary message).
# The callables are imported lazily inside the function to avoid circular
# imports at module load time.
# ---------------------------------------------------------------------------

def _dispatch(tool: str, args: dict[str, Any]) -> str:  # noqa: C901 (complexity ok)
    """Execute a single named tool with the given args dict.

    Returns a one-line summary string (no PNG rendering – only the final state
    of the canvas is rendered by the batch tool itself).
    """
    # --- drawing ---
    if tool == "draw_rect":
        from svg_mcp.tools.drawing import _draw_rect
        eid = _draw_rect(**args)
        return f"Rectangle added (id={eid})."

    if tool == "draw_circle":
        from svg_mcp.tools.drawing import _draw_circle
        eid = _draw_circle(**args)
        return f"Circle added (id={eid})."

    if tool == "draw_ellipse":
        from svg_mcp.tools.drawing import _draw_ellipse
        eid = _draw_ellipse(**args)
        return f"Ellipse added (id={eid})."

    if tool == "draw_line":
        from svg_mcp.tools.drawing import _draw_line
        eid = _draw_line(**args)
        return f"Line added (id={eid})."

    if tool == "draw_polyline":
        from svg_mcp.tools.drawing import _draw_polyline
        eid = _draw_polyline(**args)
        return f"Polyline added (id={eid})."

    if tool == "draw_polygon":
        from svg_mcp.tools.drawing import _draw_polygon
        eid = _draw_polygon(**args)
        return f"Polygon added (id={eid})."

    if tool == "draw_path":
        from svg_mcp.tools.drawing import _draw_path
        eid = _draw_path(**args)
        return f"Path added (id={eid})."

    if tool == "draw_text":
        from svg_mcp.tools.drawing import _draw_text
        eid = _draw_text(**args)
        return f"Text added (id={eid})."

    if tool == "draw_image":
        from svg_mcp.tools.drawing import _draw_image
        eid = _draw_image(**args)
        return f"Image added (id={eid})."

    if tool == "draw_group":
        from svg_mcp.tools.drawing import _draw_group
        eid = _draw_group(**args)
        return f"Group added (id={eid})."

    if tool == "draw_raw_svg":
        from svg_mcp.tools.drawing import _draw_raw_svg
        eid = _draw_raw_svg(**args)
        return f"Raw SVG added (id={eid})."

    # --- element management ---
    if tool == "update_element":
        c = _get_canvas()
        if c.update_element(args["element_id"], args["svg_fragment"]):
            return f"Element '{args['element_id']}' updated."
        return f"Element '{args['element_id']}' not found."

    if tool == "remove_element":
        c = _get_canvas()
        if c.remove_element(args["element_id"]):
            return f"Element '{args['element_id']}' removed."
        return f"Element '{args['element_id']}' not found."

    if tool == "add_def":
        _get_canvas().add_def(args["def_fragment"])
        return "Definition added to <defs>."

    # --- z-order ---
    if tool == "reorder_element":
        c = _get_canvas()
        n = len(c.elements)
        delta_map = {"forward": 1, "backward": -1, "front": n, "back": -n}
        label_map = {
            "forward": "moved forward",
            "backward": "moved backward",
            "front": "brought to front",
            "back": "sent to back",
        }
        direction = args["direction"]
        if c.move_element(args["element_id"], delta_map[direction]):
            return f"'{args['element_id']}' {label_map[direction]}."
        return f"'{args['element_id']}' not found or already at limit."

    # --- canvas management ---
    if tool == "create_canvas":
        from svg_mcp.canvas import _DEFAULT_BG, _DEFAULT_HEIGHT, _DEFAULT_WIDTH
        w = args.get("width", _DEFAULT_WIDTH)
        h = args.get("height", _DEFAULT_HEIGHT)
        bg = args.get("background", _DEFAULT_BG)
        set_canvas(Canvas(width=w, height=h, background=bg))
        return f"Canvas created ({w}×{h}, background={bg})."

    if tool == "resize_canvas":
        bg = args.get("background")
        _get_canvas().resize(args["width"], args["height"], bg)
        return (
            f"Canvas resized to {args['width']}×{args['height']}"
            + (f", background={bg}" if bg else "") + "."
        )

    if tool == "clear_canvas":
        _get_canvas().clear()
        return "Canvas cleared."

    if tool == "history":
        c = _get_canvas()
        if args["action"] == "undo":
            return "Undo successful." if c.undo() else "Nothing to undo."
        return "Redo successful." if c.redo() else "Nothing to redo."

    raise ValueError(f"Unknown tool in batch: {tool!r}")


# ---------------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------------

@mcp.tool(structured_output=False)
def batch(
    calls: list[dict[str, Any]],
) -> list[types.ContentBlock]:
    """Execute multiple tool calls in a single round-trip and return one canvas preview.

    This is the **preferred way** to draw complex scenes: instead of N separate
    tool calls (each generating an intermediate PNG), bundle all operations into
    one ``batch`` call.  Only a single canvas preview is returned — after the
    last operation completes.

    ``calls`` is a JSON array of objects, each with:
    - ``"tool"``  — the name of the tool to call (string).
    - ``"args"``  — an object whose keys match the tool's parameters (object).

    Supported tools: ``draw_rect``, ``draw_circle``, ``draw_ellipse``,
    ``draw_line``, ``draw_polyline``, ``draw_polygon``, ``draw_path``,
    ``draw_text``, ``draw_image``, ``draw_group``, ``draw_raw_svg``,
    ``update_element``, ``remove_element``, ``add_def``, ``reorder_element``,
    ``create_canvas``, ``resize_canvas``, ``clear_canvas``, ``history``.

    Example::

        batch(calls=[
            {"tool": "create_canvas", "args": {"width": 400, "height": 300}},
            {"tool": "draw_rect",     "args": {"x": 10, "y": 10, "width": 380, "height": 280, "fill": "skyblue"}},
            {"tool": "draw_text",     "args": {"x": 200, "y": 160, "text": "Hello!", "font_size": 48, "text_anchor": "middle"}},
        ])
    """
    summaries: list[str] = []
    errors: list[str] = []

    for i, call in enumerate(calls):
        tool = call.get("tool", "")
        args = call.get("args", {})
        try:
            summaries.append(_dispatch(tool, args))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Step {i + 1} ({tool}): {exc}")

    lines: list[str] = [f"Batch: {len(calls)} operation(s)."]
    for j, msg in enumerate(summaries, 1):
        lines.append(f"  {j}. {msg}")
    if errors:
        lines.append("Errors:")
        lines.extend(f"  {e}" for e in errors)

    return canvas_png_response("\n".join(lines))
