"""Minimalist theme: maximum calendar, minimum chrome.

Ultra-slim header and short two-panel bottom strip give the week view as
much vertical space as possible.  No filled bars anywhere — all-day events
are outlined, today gets a subtle underline accent.  The birthday panel is
hidden to keep the bottom strip clean; only weather and the daily quote
remain.
"""
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle


def minimalist_theme() -> Theme:
    header_h = 24                          # ultra-slim — just enough for text
    bottom_h = 100                         # compact: weather + quote only
    week_h = 480 - header_h - bottom_h     # 356px — 36px more than default
    bottom_y = header_h + week_h           # 380

    return Theme(
        name="minimalist",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, header_h),
            week_view=ComponentRegion(0, header_h, 800, week_h),
            weather=ComponentRegion(0, bottom_y, 400, bottom_h),
            birthdays=ComponentRegion(0, 0, 0, 0, visible=False),
            info=ComponentRegion(400, bottom_y, 400, bottom_h),
            draw_order=["header", "week_view", "weather", "info"],
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=False,         # plain text, thin bottom border only
            invert_today_col=False,      # underline accent instead of filled block
            invert_allday_bars=False,    # outlined bars — lighter visual weight
            spacing_scale=1.3,           # generous breathing room
            label_font_size=10,
            label_font_weight="regular",
        ),
    )
