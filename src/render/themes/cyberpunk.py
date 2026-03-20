"""Cyberpunk theme: white-on-black canvas, tight spacing, bold section labels.

This theme uses the default layout geometry but inverts the color scheme:
the canvas background is black, text and lines are drawn in white.
"""
from src.render.theme import Theme, ThemeLayout, ThemeStyle
from src.render.theme import default_layout


def cyberpunk_theme() -> Theme:
    return Theme(
        name="cyberpunk",
        layout=default_layout(),
        style=ThemeStyle(
            fg=1,                    # white text / lines on black canvas
            bg=0,                    # black background
            invert_header=False,     # canvas is already dark; bottom border line only
            invert_today_col=True,   # today column: white fill + black text (pops)
            invert_allday_bars=True, # all-day bars: white fill + black text
            spacing_scale=0.9,       # slightly tighter for a denser, information-rich feel
            label_font_size=11,
            label_font_weight="bold",
        ),
    )
