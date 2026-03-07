"""In-memory SVG canvas with undo/redo history."""

from __future__ import annotations

import base64
import copy
import uuid
from typing import Any

import cairosvg

_DEFAULT_WIDTH = 800
_DEFAULT_HEIGHT = 600
_DEFAULT_BG = "white"

# Maximum number of undo snapshots kept in memory
_MAX_HISTORY = 50


class Canvas:
    """Persistent in-memory SVG canvas that accumulates elements."""

    def __init__(
        self,
        width: int = _DEFAULT_WIDTH,
        height: int = _DEFAULT_HEIGHT,
        background: str = _DEFAULT_BG,
    ):
        self.width = width
        self.height = height
        self.background = background
        self.elements: list[dict[str, Any]] = []  # [{id, svg}]
        self.defs: list[str] = []                 # raw <defs> children
        self._history: list[dict[str, Any]] = []  # undo stack
        self._future: list[dict[str, Any]] = []   # redo stack

    # ------------------------------------------------------------------
    # History helpers
    # ------------------------------------------------------------------

    def _next_id(self, prefix: str = "el") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    def _snapshot(self) -> dict[str, Any]:
        return {
            "elements": copy.deepcopy(self.elements),
            "defs": list(self.defs),
        }

    def _push_history(self) -> None:
        self._history.append(self._snapshot())
        if len(self._history) > _MAX_HISTORY:
            self._history.pop(0)
        self._future.clear()

    def _restore(self, snapshot: dict[str, Any]) -> None:
        self.elements = snapshot["elements"]
        self.defs = snapshot["defs"]

    # ------------------------------------------------------------------
    # Undo / redo
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Element management
    # ------------------------------------------------------------------

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
        if all(e["id"] != element_id for e in self.elements):
            return False
        self._push_history()
        self.elements = [e for e in self.elements if e["id"] != element_id]
        return True

    def get_element_svg(self, element_id: str) -> str | None:
        for el in self.elements:
            if el["id"] == element_id:
                return el["svg"]
        return None

    def move_element(self, element_id: str, delta: int) -> bool:
        """Move element up (delta>0) or down (delta<0) in the z-order."""
        idx = next(
            (i for i, e in enumerate(self.elements) if e["id"] == element_id), None
        )
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

    # ------------------------------------------------------------------
    # Canvas-level mutations
    # ------------------------------------------------------------------

    def resize(self, width: int, height: int, background: str | None = None) -> None:
        """Change dimensions (and optionally background) without clearing elements."""
        self._push_history()
        self.width = width
        self.height = height
        if background is not None:
            self.background = background

    def add_def(self, def_fragment: str) -> None:
        self._push_history()
        self.defs.append(def_fragment)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

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
        parts.append(f'  <rect width="100%" height="100%" fill="{self.background}" />')
        for el in self.elements:
            parts.append(f"  {el['svg']}")
        parts.append("</svg>")
        return "\n".join(parts)

    def to_png_bytes(self, scale: float = 1.0) -> bytes:
        return cairosvg.svg2png(
            bytestring=self.to_svg().encode("utf-8"),
            output_width=int(self.width * scale),
            output_height=int(self.height * scale),
        )

    def to_png_base64(self, scale: float = 1.0) -> str:
        return base64.b64encode(self.to_png_bytes(scale)).decode("ascii")


# Global singleton – all tool modules reference this object.
# Named with a leading underscore to avoid shadowing the `svg_mcp.canvas` sub-module
# when accessed via `svg_mcp.__init__`.
_canvas_singleton = Canvas()

# Convenience alias used by older code and __init__.py exports.
canvas = _canvas_singleton


def get_canvas() -> Canvas:
    """Return the current canvas singleton.

    Always returns the up-to-date object even after ``create_canvas`` replaces it.
    Callers should use ``set_canvas`` to swap in a new instance.
    """
    return canvas


def set_canvas(new_canvas: Canvas) -> None:
    """Replace the global canvas singleton."""
    global canvas
    canvas = new_canvas
