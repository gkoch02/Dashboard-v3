"""Minimalist theme: no filled header bar, slim header, generous event spacing.

The calendar gets extra vertical room (340px vs 320px) by trimming the header
to 30px. All-day events show as bordered outlines rather than solid filled bars.
Section labels are rendered in regular weight for a lighter look.
"""
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle


def minimalist_theme() -> Theme:
    return Theme(
        name="minimalist",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, 30),
            week_view=ComponentRegion(0, 30, 800, 340),
            weather=ComponentRegion(0, 370, 266, 110),
            birthdays=ComponentRegion(266, 370, 267, 110),
            info=ComponentRegion(533, 370, 267, 110),
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=False,        # plain text header, no filled bar
            invert_today_col=True,
            invert_allday_bars=False,   # outlined bars instead of solid filled
            spacing_scale=1.4,          # more breathing room between events
            label_font_size=11,
            label_font_weight="regular",
        ),
    )
