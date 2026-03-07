"""Shared response builder and SVG attribute helpers."""

from __future__ import annotations

from mcp import types

from svg_mcp.canvas import get_canvas


def canvas_png_response(message: str = "") -> list[types.ContentBlock]:
    """Return a text block (optional) followed by the current canvas as a PNG.

    Always calls ``get_canvas()`` at call-time so that a canvas replacement
    (e.g. via ``create_canvas``) is immediately reflected in the preview.
    """
    blocks: list[types.ContentBlock] = []
    if message:
        blocks.append(types.TextContent(type="text", text=message))
    blocks.append(
        types.ImageContent(
            type="image",
            data=get_canvas().to_png_base64(),
            mimeType="image/png",
        )
    )
    return blocks


def style_attrs(
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
    opacity: float | None = None,
    stroke_dasharray: str | None = None,
    extra: dict[str, str] | None = None,
) -> str:
    """Build an SVG attribute string from common style parameters."""
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
