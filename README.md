# svg-mcp

An MCP server that provides a persistent SVG canvas you can draw on with simple tool calls. Every tool returns the current canvas as a PNG image so you can visually inspect progress after each step.

## Features

- Persistent in-memory canvas — elements accumulate across tool calls
- Shape tools for rectangles, circles, ellipses, lines, polylines, polygons, paths, and text
- `draw_raw_svg` escape hatch for any arbitrary SVG fragment
- `add_def` for gradients, patterns, clip-paths, and filters
- Export to **SVG** or **PNG** (with configurable resolution scale)
- Every tool returns the current canvas as a PNG preview

## Requirements

- Python ≥ 3.14
- [Cairo](https://www.cairographics.org/) system library (used by `cairosvg` for PNG rendering)

On Ubuntu/Debian:
```sh
sudo apt install libcairo2
```

On macOS (Homebrew):
```sh
brew install cairo
```

Python dependencies:
```sh
pip install cairosvg "mcp[cli]"
```

## Running the server

The server communicates over **stdio** (standard MCP transport):

```sh
python main.py
```

## MCP client configuration

### With Nix (recommended)

If you have [Nix](https://nixos.org/) installed, no local checkout is required. Use `nix run` as the command — Nix will fetch, build, and cache everything automatically.

#### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "nix",
      "args": ["run", "github:datakurre/svg-mcp"]
    }
  }
}
```

#### VS Code (`settings.json`)

```json
{
  "mcp": {
    "servers": {
      "svg-mcp": {
        "type": "stdio",
        "command": "nix",
        "args": ["run", "github:datakurre/svg-mcp"]
      }
    }
  }
}
```

### Without Nix (local Python)

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "svg-mcp": {
      "command": "python",
      "args": ["/path/to/svg-mcp/main.py"]
    }
  }
}
```

### VS Code (`settings.json`)

```json
{
  "mcp": {
    "servers": {
      "svg-mcp": {
        "type": "stdio",
        "command": "python",
        "args": ["/path/to/svg-mcp/main.py"]
      }
    }
  }
}
```

Replace `/path/to/svg-mcp/main.py` with the absolute path on your machine.

## Tools reference

### Canvas management

| Tool | Description |
|---|---|
| `create_canvas(width, height, background)` | Create or reset the canvas. Default: 800×600, white background. |
| `clear_canvas()` | Remove all elements (and defs), keeping size and background. |
| `get_canvas()` | Return a PNG preview of the current canvas with no changes. |
| `get_svg_source()` | Return the raw SVG source of the current canvas. |
| `list_elements()` | List all element IDs on the canvas. |
| `remove_element(element_id)` | Remove a single element by its ID. |

### Drawing

| Tool | Key parameters |
|---|---|
| `draw_rect` | `x, y, width, height, rx, ry, fill, stroke, stroke_width, opacity, rotation` |
| `draw_circle` | `cx, cy, r, fill, stroke, stroke_width, opacity` |
| `draw_ellipse` | `cx, cy, rx, ry, fill, stroke, stroke_width, opacity, rotation` |
| `draw_line` | `x1, y1, x2, y2, stroke, stroke_width, opacity, stroke_linecap` |
| `draw_polyline` | `points` (e.g. `"0,0 50,50 100,0"`), fill, stroke, … |
| `draw_polygon` | `points` (closed shape), fill, stroke, … |
| `draw_path` | `d` (SVG path data), fill, stroke, … |
| `draw_text` | `x, y, text, font_size, font_family, fill, text_anchor, font_weight, rotation` |
| `draw_image` | `x, y, width, height, href` (URL or data-URI) |
| `draw_raw_svg` | `svg_fragment` — any valid SVG string, e.g. `<g>`, `<use>`, filters |

All drawing tools accept an optional `element_id` parameter. If omitted, a unique ID is generated automatically.

### Definitions

| Tool | Description |
|---|---|
| `add_def(def_fragment)` | Add a `<defs>` child such as a gradient, pattern, or clip-path. |

Example — define a linear gradient and use it:

```
add_def('<linearGradient id="sky"><stop offset="0%" stop-color="#87ceeb"/><stop offset="100%" stop-color="#fff"/></linearGradient>')
draw_rect(x=0, y=0, width=800, height=600, fill="url(#sky)")
```

### Export

| Tool | Description |
|---|---|
| `export_svg(file_path)` | Write the canvas to an `.svg` file. |
| `export_png(file_path, scale)` | Write the canvas to a `.png` file. `scale=2.0` doubles the resolution. |

## Example session

```
create_canvas(width=600, height=400, background="#1a1a2e")
draw_circle(cx=300, cy=200, r=120, fill="#e94560", stroke="white", stroke_width=3)
draw_text(x=300, y=210, text="Hello!", font_size=48, fill="white", text_anchor="middle")
export_png("output/hello.png", scale=2.0)
```

## Coordinate system

SVG uses a **top-left origin** with y increasing downward. All units are pixels relative to the canvas dimensions set in `create_canvas`.