# AGENTS.md — svg-mcp developer guide for AI agents

This file is the primary reference for AI coding agents (Copilot, Claude, etc.) working inside this repository. Read it before making any changes.

---

## What this project is

`svg-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes a **persistent in-memory SVG canvas** as a set of tool calls. Every tool returns the current canvas rendered as a **PNG image** so the calling agent can visually inspect progress after each step. The server is built with [FastMCP](https://github.com/jlowin/fastmcp); SVG element construction and PNG rasterisation are handled by [`drawsvg`](https://github.com/cduck/drawsvg) (the `drawsvg[raster]` extra pulls in the Cairo backend).

---

## Repository layout

```
main.py                        Entry point — runs the MCP server over stdio
pyproject.toml                 Package metadata and dependencies
src/
  svg_mcp/
    __init__.py                Imports tools (side-effect: registers them) + re-exports mcp
    server.py                  FastMCP instance + system-prompt INSTRUCTIONS string
    canvas.py                  Canvas class, global singleton, get_canvas()/set_canvas()
    _helpers.py                canvas_png_response() shared by all tools
    tools/
      __init__.py              Imports all tool sub-modules to trigger @mcp.tool() registration
      batch.py                 batch(calls) — multi-operation tool (preferred for drawing)
      canvas_mgmt.py           create_canvas, resize_canvas, inspect, clear_canvas, export
      drawing.py               draw_rect, draw_circle, draw_ellipse, draw_line,
                               draw_polyline, draw_polygon, draw_path, draw_text,
                               draw_image, draw_group, draw_raw_svg
                               (also exports private _draw_* core functions used by batch)
      elements.py              update_element, remove_element, add_def
      history.py               history(action="undo"|"redo")
      zorder.py                reorder_element(element_id, direction)
```

---

## Architecture: the canvas singleton

`canvas.py` owns a **module-level singleton** of type `Canvas`. Because `create_canvas` must be able to swap in a brand-new `Canvas` object, the singleton is accessed through two accessor functions — never through a direct import of the object itself:

```python
# canvas.py
def get_canvas() -> Canvas: ...   # always returns the live instance
def set_canvas(new: Canvas) -> None: ...  # swaps the singleton
```

**Every tool file must call `get_canvas()` at invocation time.** Storing a reference to the canvas at import time will silently break after `create_canvas` is called, because the tool will keep drawing on the discarded old object and return blank previews.

```python
# CORRECT — dereferences at call time
from svg_mcp.canvas import get_canvas as _get_canvas
eid = _get_canvas().add_element(svg, element_id)

# WRONG — stale reference after create_canvas()
from svg_mcp.canvas import canvas as _canvas   # ← don't do this
eid = _canvas.add_element(svg, element_id)
```

The same rule applies in `_helpers.py`: `canvas_png_response()` must call `get_canvas()` each time, not hold a cached reference.

---

## The `Canvas` class (canvas.py)

| Method | Purpose |
|---|---|
| `add_element(svg, element_id=None) → str` | Append an SVG fragment; returns the element ID |
| `update_element(element_id, svg) → bool` | Replace a fragment in-place (same z-position) |
| `remove_element(element_id) → bool` | Delete by ID |
| `get_element_svg(element_id) → str \| None` | Retrieve a fragment |
| `move_element(element_id, delta) → bool` | Shift z-order by `delta` steps (+up, −down) |
| `clear()` | Remove all elements and defs |
| `resize(w, h, background=None)` | Change dimensions without clearing |
| `add_def(fragment)` | Append to the `<defs>` block |
| `to_svg() → str` | Render the full SVG document |
| `to_png_bytes(scale=1.0) → bytes` | Rasterise via `drawsvg.Drawing.rasterize()` |
| `to_png_base64(scale=1.0) → str` | Base64-encoded PNG for tool responses |

Every mutating method calls `_push_history()` first, enabling undo/redo up to 50 steps.

---

## Adding a new tool

1. Pick the right sub-module under `src/svg_mcp/tools/` or create a new one.
2. Decorate the function with `@mcp.tool()` (import `mcp` from `svg_mcp.server`).
3. Import `get_canvas` from `svg_mcp.canvas` — **never import `canvas` directly**.
4. Return `canvas_png_response("…message…")` (from `svg_mcp._helpers`) so callers always get a live preview.
5. If you add a new sub-module, import it in `src/svg_mcp/tools/__init__.py`.
6. Update the `INSTRUCTIONS` string in `server.py` to document the new tool.

Minimal template:

```python
from fastmcp.utilities.types import Image
from svg_mcp._helpers import canvas_png_response
from svg_mcp.canvas import get_canvas as _get_canvas
from svg_mcp.server import mcp

@mcp.tool
def my_tool(param: str) -> list[str | Image]:
    """One-line description shown to the agent."""
    result = _get_canvas().some_method(param)
    return canvas_png_response(f"Done: {result}.")
```

---

## Tool inventory (22 tools)

### Batch (`batch.py`) — preferred entry point

| Tool | Signature | Notes |
|---|---|---|
| `batch` | `(calls: list[dict])` | Execute multiple operations in one round-trip; returns a single canvas preview |

Each element of `calls` is `{"tool": "<name>", "args": {...}}`. Supported tool names mirror
all drawing and element-management tools (see sections below), plus `create_canvas`,
`resize_canvas`, `clear_canvas`, and `history`.

Internally, `batch.py` imports the private `_draw_*` core functions from `drawing.py`
(lazy imports inside `_dispatch` to avoid circular imports at module load time).

### Canvas management (`canvas_mgmt.py`)

| Tool | Signature | Notes |
|---|---|---|
| `create_canvas` | `(width=800, height=600, background="white")` | Replaces the global canvas singleton via `set_canvas()` |
| `resize_canvas` | `(width, height, background=None)` | Mutates in-place; elements are preserved |
| `inspect` | `(what, element_id=None)` | `what` ∈ `"canvas"/"svg"/"elements"/"element"` |
| `clear_canvas` | `()` | Removes all elements and defs; keeps dimensions |
| `export` | `(file_path, format="svg", scale=1.0)` | `format` ∈ `"svg"/"png"` — **SVG is the default** |

### Drawing (`drawing.py`)

Each shape tool is implemented as a private `_draw_*` core function (no MCP dependency)
wrapped by a `@mcp.tool()` function. The `batch` tool imports and calls the core functions
directly. All drawing tools accept `element_id` (auto-generated UUID suffix if omitted),
`fill`, `stroke`, `stroke_width`, `stroke_dasharray`, and `opacity`.

| Tool | Shape-specific params |
|---|---|
| `draw_rect` | `x, y, width, height, rx, ry, rotation` |
| `draw_circle` | `cx, cy, r` |
| `draw_ellipse` | `cx, cy, rx, ry, rotation` |
| `draw_line` | `x1, y1, x2, y2, stroke_linecap` |
| `draw_polyline` | `points` (space-separated `"x,y"` pairs, open shape) |
| `draw_polygon` | `points` (closed shape) |
| `draw_path` | `d` (SVG path data string); **or** arc convenience params: `arc_cx, arc_cy, arc_r, arc_start_deg, arc_end_deg, arc_cw` — provide one mode or the other, never both |
| `draw_text` | `x, y, text, font_size, font_family, text_anchor, font_weight, rotation` |
| `draw_image` | `x, y, width, height, href` (URL or data-URI) |
| `draw_group` | `children` (raw SVG string), `transform`, `opacity` |
| `draw_raw_svg` | `svg_fragment` (any valid SVG string) |

### Element management (`elements.py`)

| Tool | Notes |
|---|---|
| `update_element(element_id, svg_fragment)` | Preserves z-order; use `inspect(what="element", element_id=…)` first |
| `remove_element(element_id)` | Permanent; use `history(action="undo")` to reverse |
| `add_def(def_fragment="", kind="", def_id="", params="")` | Appends to `<defs>`. **Raw mode**: pass `def_fragment` as a literal SVG string. **Typed mode**: set `kind` to one of `linear_gradient`, `radial_gradient`, `pattern`, `clip_path`, or `marker`; provide `def_id` and a JSON string in `params` (see source for field names). IDs in defs can be referenced via `fill="url(#id)"`. |

### History (`history.py`)

| Tool | Notes |
|---|---|
| `history(action)` | `action` ∈ `"undo"/"redo"` — up to 50 undo steps |

### Z-order (`zorder.py`)

| Tool | Notes |
|---|---|
| `reorder_element(element_id, direction)` | `direction` ∈ `"forward"/"backward"/"front"/"back"` |

---

## `_helpers.py` — shared utilities

**`canvas_png_response(message="")`**  
Builds the standard `list[str | Image]` return value: an optional `str` text block followed by a `fastmcp.utilities.types.Image` block (PNG preview). Always call `get_canvas()` inside — never cache the canvas reference here.

> `style_attrs()` was removed in the drawsvg refactor. SVG attribute strings are no longer built by hand; use drawsvg constructor keyword arguments instead.

---

## drawsvg integration

All SVG elements are built with [`drawsvg`](https://github.com/cduck/drawsvg) constructors rather than f-string concatenation, and the canvas is rasterised via `drawsvg[raster]` (Cairo-backed) instead of `cairosvg`.

### Element serialisation — `_elem_svg()` in `drawing.py`

`drawsvg` elements do not expose a simple `.as_svg()` method on their own. The private helper `_elem_svg(elem)` serialises any `DrawingElement` by:

1. Creating a temporary `drawsvg.Drawing(1, 1)`,
2. Calling `tmp.append(elem)`,
3. Getting `tmp.as_svg()` and stripping the wrapper (`<?xml …>`, `<svg …>`, `</svg>`, `<defs>…</defs>`),
4. Returning the trimmed fragment string.

### drawsvg element quirks to be aware of

| drawsvg call | Actual SVG output |
|---|---|
| `drawsvg.Line(x1, y1, x2, y2)` | `<path d="M{x1},{y1} L{x2},{y2}">` (NOT `<line>`) |
| `drawsvg.Lines(*coords, close=False)` | `<path …>` (NOT `<polyline>`) |
| `drawsvg.Lines(*coords, close=True)` | `<path …>` (NOT `<polygon>`) |
| `drawsvg.Image(x, y, w, h, path=href)` | Uses `xlink:href` attribute (NOT `href`) |
| `drawsvg.Text(text, size, x, y)` | Auto-HTML-escapes content; do **not** pre-escape |
| `drawsvg.Arc(cx, cy, r, start, end, cw=…)` | `<path d="… A …">` (SVG arc command) |

### Rasterisation

```python
# canvas.py  to_png_bytes()
d = drawsvg.Drawing(self.width, self.height)
d.set_pixel_scale(scale)           # only when scale != 1.0
d.append_def(drawsvg.Raw(def_frag))
d.append(drawsvg.Raw(element_svg))
return d.rasterize().png_data      # bytes
```

### Typed defs — `add_def` typed mode

When `kind` is set, `add_def` builds a drawsvg object and extracts its `<defs>` fragment via `_def_elem_to_svg()` (parallel helper to `_elem_svg`, using `tmp.append_def(elem)` + regex on `tmp.as_svg()`).

Supported `kind` values and their `params` JSON fields:

| `kind` | Required `params` fields |
|---|---|
| `linear_gradient` | `x1, y1, x2, y2` (0–1), `stops` list `{offset, color[, opacity]}`, optional `units` |
| `radial_gradient` | `cx, cy, r, fx, fy` (0–1), `stops` list, optional `units` |
| `pattern` | `width, height`, `children` (SVG fragment string), optional `units`, `content_units` |
| `clip_path` | `children` (SVG fragment string) |
| `marker` | `width, height`, `children` (SVG fragment string), optional `orient`, `units` |

### Dependencies

Only two runtime dependencies (see `pyproject.toml`):

```toml
dependencies = [
    "drawsvg[raster]>=2.4.1",
    "fastmcp>=3.1.0",
]
```

`cairosvg` and the bare `mcp` package have been removed.

---

## Key invariants to maintain

1. **Every tool returns a PNG preview.** Use `canvas_png_response()` — never return plain text or `None`.
2. **Every mutation is history-tracked.** `Canvas` methods call `_push_history()` before changing state. New `Canvas` methods must do the same.
3. **`get_canvas()` — always, everywhere.** No module-level or function-signature-default references to the canvas object.
4. **Tool registration is by import side-effect.** `@mcp.tool()` on the function is sufficient — just make sure the module is imported in `tools/__init__.py`.
5. **IDs are stable.** An element's `element_id` does not change after creation. Tools that accept `element_id` as input rely on this.

---

## Running and testing

```sh
# Run the MCP server (stdio transport)
PYTHONPATH=src python main.py

# Quick sanity check — counts registered tools
PYTHONPATH=src python -c "
import asyncio, svg_mcp
tools = asyncio.run(svg_mcp.mcp.list_tools())
print(len(tools), 'tools:', [t.name for t in tools])
"

# Run the test suite
PYTHONPATH=src pytest
```

Dependencies require the Cairo system library (`libcairo2` on Debian/Ubuntu, `cairo` via Homebrew on macOS). Python ≥ 3.14 is required.
