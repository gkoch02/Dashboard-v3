"""Old Fashioned theme: dominant header, side-by-side layout (calendar left, info right).

The calendar occupies the left 62% of the canvas; weather, birthdays, and the
daily quote are stacked in a right column.  The header is taller and more
formal-looking.

NOTE: A serif font (e.g. Lora) would complete this theme.  To enable it:
  1. Place LoraBold.ttf and LoraRegular.ttf in the fonts/ directory.
  2. Add accessor functions to src/render/fonts.py following the existing pattern.
  3. Uncomment the font_* lines below and import those accessors.

Until the font files are present this theme uses the default Plus Jakarta Sans family.
"""
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle


def old_fashioned_theme() -> Theme:
    return Theme(
        name="old_fashioned",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, 56),           # tall decorative header
            week_view=ComponentRegion(0, 56, 500, 424),       # left 62%: full-height calendar
            weather=ComponentRegion(500, 56, 300, 142),       # right column: weather
            birthdays=ComponentRegion(500, 198, 300, 142),    # right column: birthdays
            info=ComponentRegion(500, 340, 300, 140),         # right column: quote
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=True,
            invert_today_col=True,
            invert_allday_bars=True,
            spacing_scale=1.1,          # slightly airier than default
            label_font_size=12,
            label_font_weight="bold",
            # font_regular=lora_regular,  # uncomment when serif font is available
            # font_bold=lora_bold,
        ),
    )
