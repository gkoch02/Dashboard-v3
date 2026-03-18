"""Tests for src/render/fonts.py — font loader functions."""

from PIL import ImageFont

from src.render.fonts import (
    bold,
    medium,
    regular,
    semibold,
    weather_icon,
)


class TestFontAccessors:
    """Smoke tests — verify each font accessor loads without error."""

    def test_regular(self):
        assert isinstance(regular(12), ImageFont.FreeTypeFont)

    def test_medium(self):
        assert isinstance(medium(12), ImageFont.FreeTypeFont)

    def test_semibold(self):
        assert isinstance(semibold(12), ImageFont.FreeTypeFont)

    def test_bold(self):
        assert isinstance(bold(12), ImageFont.FreeTypeFont)

    def test_weather_icon(self):
        assert isinstance(weather_icon(20), ImageFont.FreeTypeFont)

    def test_caching_returns_same_object(self):
        """@lru_cache should return the same object on repeated calls."""
        f1 = regular(12)
        f2 = regular(12)
        assert f1 is f2
