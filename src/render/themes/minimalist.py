"""Minimalist theme: editorial calm — the calendar owns the screen.

Ultra-slim 22px header (single pixel underline, no filled bar). Week view
gets 362px — 42px more than the default. A compact 96px bottom strip holds
only weather and the daily quote side-by-side; birthdays are hidden to keep
the layout uncluttered. Today is marked with a subtle double underline, not
a filled column. All-day event bars are outlined rather than filled.

Uses DM Sans — a screen-optimised variable geometric sans with per-size
optical tuning — for an editorial, precision feel that's distinct from the
warmer Plus Jakarta Sans used in the default theme.
"""
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle
from src.render.fonts import dm_regular, dm_medium, dm_semibold, dm_bold


def minimalist_theme() -> Theme:
    header_h = 22
    bottom_h = 96
    week_h = 480 - header_h - bottom_h     # 362px
    bottom_y = header_h + week_h            # 384

    return Theme(
        name="minimalist",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, header_h),
            week_view=ComponentRegion(0, header_h, 800, week_h),
            weather=ComponentRegion(0, bottom_y, 420, bottom_h),
            birthdays=ComponentRegion(0, 0, 0, 0, visible=False),
            info=ComponentRegion(420, bottom_y, 380, bottom_h),
            draw_order=["header", "week_view", "weather", "info"],
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=False,          # single pixel underline only
            invert_today_col=False,       # double underline accent, no filled block
            invert_allday_bars=False,     # outlined bars — lighter visual weight
            spacing_scale=1.4,
            label_font_size=9,
            label_font_weight="regular",
            font_regular=dm_regular,
            font_medium=dm_medium,
            font_semibold=dm_semibold,
            font_bold=dm_bold,
        ),
    )
