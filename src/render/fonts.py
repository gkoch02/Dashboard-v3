from functools import lru_cache
from pathlib import Path
from PIL import ImageFont

FONT_DIR = Path(__file__).parent.parent.parent / "fonts"


@lru_cache(maxsize=32)
def get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


@lru_cache(maxsize=32)
def _get_variable_font(name: str, size: int, wght: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_DIR / name), size)
    font.set_variation_by_axes([wght])
    return font


# Convenience accessors — Plus Jakarta Sans (warm geometric)
def regular(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlusJakartaSans-Regular.ttf", size)


def medium(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlusJakartaSans-Medium.ttf", size)


def semibold(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlusJakartaSans-SemiBold.ttf", size)


def bold(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlusJakartaSans-Bold.ttf", size)


def weather_icon(size: int) -> ImageFont.FreeTypeFont:
    return get_font("weathericons-regular.ttf", size)


# Share Tech Mono — monospace terminal font for the Cyberpunk theme.
# Single weight; all four callables use the same file for theme compatibility.
def cyber_mono(size: int) -> ImageFont.FreeTypeFont:
    return get_font("ShareTechMono-Regular.ttf", size)


# Playfair Display — newspaper serif font for the Old Fashioned theme.
def playfair_regular(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlayfairDisplay-Regular.ttf", size)


def playfair_medium(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlayfairDisplay-Medium.ttf", size)


def playfair_semibold(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlayfairDisplay-SemiBold.ttf", size)


def playfair_bold(size: int) -> ImageFont.FreeTypeFont:
    return get_font("PlayfairDisplay-Bold.ttf", size)
