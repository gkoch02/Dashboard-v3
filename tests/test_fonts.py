"""Tests for src/render/fonts.py — font loader functions."""

from PIL import ImageFont

from src.render.fonts import (
    barlow_condensed_medium,
    barlow_condensed_semibold,
    bold,
    fraunces_bold,
    inter_bold,
    lora_italic,
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

    def test_inter_bold(self):
        assert isinstance(inter_bold(12), ImageFont.FreeTypeFont)

    def test_weather_icon(self):
        assert isinstance(weather_icon(20), ImageFont.FreeTypeFont)

    def test_fraunces_bold(self):
        assert isinstance(fraunces_bold(24), ImageFont.FreeTypeFont)

    def test_barlow_condensed_medium(self):
        assert isinstance(barlow_condensed_medium(12), ImageFont.FreeTypeFont)

    def test_barlow_condensed_semibold(self):
        assert isinstance(barlow_condensed_semibold(12), ImageFont.FreeTypeFont)

    def test_lora_italic(self):
        assert isinstance(lora_italic(14), ImageFont.FreeTypeFont)

    def test_caching_returns_same_object(self):
        """@lru_cache should return the same object on repeated calls."""
        f1 = regular(12)
        f2 = regular(12)
        assert f1 is f2
