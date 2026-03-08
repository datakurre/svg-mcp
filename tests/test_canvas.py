"""Tests for the Canvas class (canvas.py)."""

import pytest

from svg_mcp.canvas import _DEFAULT_BG, _DEFAULT_HEIGHT, _DEFAULT_WIDTH, Canvas

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestCanvasInit:
    def test_defaults(self):
        c = Canvas()
        assert c.width == _DEFAULT_WIDTH
        assert c.height == _DEFAULT_HEIGHT
        assert c.background == _DEFAULT_BG
        assert c.elements == []
        assert c.defs == []

    def test_custom_dimensions(self):
        c = Canvas(width=400, height=300, background="black")
        assert c.width == 400
        assert c.height == 300
        assert c.background == "black"


# ---------------------------------------------------------------------------
# add_element
# ---------------------------------------------------------------------------


class TestAddElement:
    def test_returns_auto_id(self):
        c = Canvas()
        eid = c.add_element("<rect/>")
        assert eid.startswith("el-")
        assert len(eid) == len("el-") + 8

    def test_respects_explicit_id(self):
        c = Canvas()
        eid = c.add_element("<circle/>", element_id="my-circle")
        assert eid == "my-circle"

    def test_element_is_stored(self):
        c = Canvas()
        c.add_element("<rect/>", element_id="r1")
        assert len(c.elements) == 1
        assert c.elements[0]["id"] == "r1"
        assert c.elements[0]["svg"] == "<rect/>"

    def test_multiple_elements_ordered(self):
        c = Canvas()
        c.add_element("<a/>", "a")
        c.add_element("<b/>", "b")
        assert [e["id"] for e in c.elements] == ["a", "b"]

    def test_add_pushes_history(self):
        c = Canvas()
        c.add_element("<rect/>")
        assert len(c._history) == 1


# ---------------------------------------------------------------------------
# update_element
# ---------------------------------------------------------------------------


class TestUpdateElement:
    def test_updates_in_place(self):
        c = Canvas()
        c.add_element("<old/>", "el")
        assert c.update_element("el", "<new/>") is True
        assert c.get_element_svg("el") == "<new/>"

    def test_preserves_z_order(self):
        c = Canvas()
        c.add_element("<a/>", "a")
        c.add_element("<b/>", "b")
        c.add_element("<c/>", "c")
        c.update_element("b", "<B/>")
        assert [e["id"] for e in c.elements] == ["a", "b", "c"]

    def test_returns_false_for_missing(self):
        c = Canvas()
        assert c.update_element("nonexistent", "<x/>") is False

    def test_update_pushes_history(self):
        c = Canvas()
        c.add_element("<old/>", "el")
        history_before = len(c._history)
        c.update_element("el", "<new/>")
        assert len(c._history) == history_before + 1


# ---------------------------------------------------------------------------
# remove_element
# ---------------------------------------------------------------------------


class TestRemoveElement:
    def test_removes_existing(self):
        c = Canvas()
        c.add_element("<rect/>", "r")
        assert c.remove_element("r") is True
        assert c.elements == []

    def test_returns_false_for_missing(self):
        c = Canvas()
        assert c.remove_element("ghost") is False

    def test_does_not_push_history_on_miss(self):
        c = Canvas()
        # history starts empty
        c.remove_element("ghost")
        assert c._history == []

    def test_remove_pushes_history(self):
        c = Canvas()
        c.add_element("<rect/>", "r")
        history_len = len(c._history)
        c.remove_element("r")
        assert len(c._history) == history_len + 1


# ---------------------------------------------------------------------------
# get_element_svg
# ---------------------------------------------------------------------------


class TestGetElementSvg:
    def test_returns_svg_for_known_id(self):
        c = Canvas()
        c.add_element("<circle/>", "c1")
        assert c.get_element_svg("c1") == "<circle/>"

    def test_returns_none_for_unknown_id(self):
        c = Canvas()
        assert c.get_element_svg("nope") is None


# ---------------------------------------------------------------------------
# move_element (z-order)
# ---------------------------------------------------------------------------


class TestMoveElement:
    def setup_method(self):
        self.c = Canvas()
        for name in ["a", "b", "c", "d"]:
            self.c.add_element(f"<{name}/>", name)

    def _order(self):
        return [e["id"] for e in self.c.elements]

    def test_move_forward(self):
        self.c.move_element("a", 1)
        assert self._order() == ["b", "a", "c", "d"]

    def test_move_backward(self):
        self.c.move_element("c", -1)
        assert self._order() == ["a", "c", "b", "d"]

    def test_move_to_front(self):
        n = len(self.c.elements)
        self.c.move_element("a", n)
        assert self._order()[-1] == "a"

    def test_move_to_back(self):
        n = len(self.c.elements)
        self.c.move_element("d", -n)
        assert self._order()[0] == "d"

    def test_clamps_at_boundary(self):
        self.c.move_element("a", -10)
        assert self._order()[0] == "a"

    def test_returns_false_already_at_limit(self):
        assert self.c.move_element("a", -1) is False

    def test_returns_false_for_unknown(self):
        assert self.c.move_element("x", 1) is False

    def test_pushes_history_on_success(self):
        before = len(self.c._history)
        self.c.move_element("a", 1)
        assert len(self.c._history) == before + 1


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


class TestClear:
    def test_removes_all_elements(self):
        c = Canvas()
        c.add_element("<a/>", "a")
        c.add_element("<b/>", "b")
        c.clear()
        assert c.elements == []

    def test_removes_defs(self):
        c = Canvas()
        c.add_def("<linearGradient id='g'/>")
        c.clear()
        assert c.defs == []

    def test_pushes_history(self):
        c = Canvas()
        c.add_element("<a/>", "a")
        before = len(c._history)
        c.clear()
        assert len(c._history) == before + 1


# ---------------------------------------------------------------------------
# resize
# ---------------------------------------------------------------------------


class TestResize:
    def test_changes_dimensions(self):
        c = Canvas()
        c.resize(1920, 1080)
        assert c.width == 1920
        assert c.height == 1080

    def test_preserves_background_when_none(self):
        c = Canvas(background="red")
        c.resize(100, 100)
        assert c.background == "red"

    def test_changes_background_when_given(self):
        c = Canvas(background="red")
        c.resize(100, 100, background="blue")
        assert c.background == "blue"

    def test_preserves_elements(self):
        c = Canvas()
        c.add_element("<rect/>", "r")
        c.resize(400, 400)
        assert len(c.elements) == 1

    def test_pushes_history(self):
        c = Canvas()
        before = len(c._history)
        c.resize(10, 10)
        assert len(c._history) == before + 1


# ---------------------------------------------------------------------------
# add_def
# ---------------------------------------------------------------------------


class TestAddDef:
    def test_appends_def(self):
        c = Canvas()
        c.add_def("<linearGradient id='g'/>")
        assert len(c.defs) == 1
        assert "linearGradient" in c.defs[0]

    def test_multiple_defs(self):
        c = Canvas()
        c.add_def("<a/>")
        c.add_def("<b/>")
        assert len(c.defs) == 2

    def test_pushes_history(self):
        c = Canvas()
        before = len(c._history)
        c.add_def("<filter/>")
        assert len(c._history) == before + 1


# ---------------------------------------------------------------------------
# Undo / redo
# ---------------------------------------------------------------------------


class TestUndoRedo:
    def test_undo_reverses_add(self):
        c = Canvas()
        c.add_element("<rect/>", "r")
        c.undo()
        assert c.elements == []

    def test_redo_reapplies_add(self):
        c = Canvas()
        c.add_element("<rect/>", "r")
        c.undo()
        c.redo()
        assert len(c.elements) == 1

    def test_undo_returns_false_when_empty(self):
        c = Canvas()
        assert c.undo() is False

    def test_redo_returns_false_when_empty(self):
        c = Canvas()
        assert c.redo() is False

    def test_new_action_clears_redo_stack(self):
        c = Canvas()
        c.add_element("<a/>", "a")
        c.undo()
        c.add_element("<b/>", "b")
        assert c.redo() is False

    def test_undo_multiple_steps(self):
        c = Canvas()
        c.add_element("<a/>", "a")
        c.add_element("<b/>", "b")
        c.undo()
        assert len(c.elements) == 1
        c.undo()
        assert len(c.elements) == 0

    def test_history_capped_at_max(self):
        from svg_mcp.canvas import _MAX_HISTORY

        c = Canvas()
        for i in range(_MAX_HISTORY + 10):
            c.add_element(f"<el{i}/>")
        assert len(c._history) <= _MAX_HISTORY


# ---------------------------------------------------------------------------
# to_svg
# ---------------------------------------------------------------------------


class TestToSvg:
    def test_contains_svg_root(self):
        c = Canvas(width=100, height=50)
        svg = c.to_svg()
        assert '<svg xmlns="http://www.w3.org/2000/svg"' in svg
        assert 'width="100"' in svg
        assert 'height="50"' in svg

    def test_background_rect_present(self):
        c = Canvas(background="navy")
        svg = c.to_svg()
        assert 'fill="navy"' in svg

    def test_elements_included(self):
        c = Canvas()
        c.add_element('<circle cx="10" cy="10" r="5"/>', "c1")
        svg = c.to_svg()
        assert '<circle cx="10" cy="10" r="5"/>' in svg

    def test_defs_included(self):
        c = Canvas()
        c.add_def('<linearGradient id="g"/>')
        svg = c.to_svg()
        assert "<defs>" in svg
        assert "linearGradient" in svg

    def test_no_defs_section_when_empty(self):
        c = Canvas()
        svg = c.to_svg()
        assert "<defs>" not in svg

    def test_viewbox_matches_dimensions(self):
        c = Canvas(width=200, height=100)
        svg = c.to_svg()
        assert 'viewBox="0 0 200 100"' in svg


# ---------------------------------------------------------------------------
# to_png_bytes / to_png_base64
# ---------------------------------------------------------------------------


class TestRendering:
    def test_to_png_bytes_returns_bytes(self):
        c = Canvas(width=10, height=10)
        result = c.to_png_bytes()
        assert isinstance(result, bytes)
        assert result[:4] == b"\x89PNG"  # PNG magic bytes

    def test_to_png_base64_is_valid_base64(self):
        import base64

        c = Canvas(width=10, height=10)
        b64 = c.to_png_base64()
        decoded = base64.b64decode(b64)
        assert decoded[:4] == b"\x89PNG"

    def test_scale_affects_output_size(self):
        c = Canvas(width=10, height=10)
        small = c.to_png_bytes(scale=1.0)
        large = c.to_png_bytes(scale=2.0)
        assert len(large) > len(small)
