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


def inter_bold(size: int) -> ImageFont.FreeTypeFont:
    return get_font("Inter-Bold.ttf", size)


def weather_icon(size: int) -> ImageFont.FreeTypeFont:
    return get_font("weathericons-regular.ttf", size)


# Fraunces Bold — display serif for large day numbers
def fraunces_bold(size: int) -> ImageFont.FreeTypeFont:
    return _get_variable_font("Fraunces-Bold.ttf", size, 700)


# Barlow Condensed — space-efficient sans for event titles
def barlow_condensed_medium(size: int) -> ImageFont.FreeTypeFont:
    return get_font("BarlowCondensed-Medium.ttf", size)


def barlow_condensed_semibold(size: int) -> ImageFont.FreeTypeFont:
    return get_font("BarlowCondensed-SemiBold.ttf", size)


# Lora Italic — editorial serif for quotes
def lora_italic(size: int) -> ImageFont.FreeTypeFont:
    return get_font("Lora-Italic.ttf", size)
