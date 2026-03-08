"""Shared fixtures for svg-mcp tests."""

import pytest

from svg_mcp.canvas import Canvas, set_canvas


@pytest.fixture(autouse=True)
def fresh_canvas():
    """Reset the global canvas singleton before every test."""
    set_canvas(Canvas(width=800, height=600, background="white"))
