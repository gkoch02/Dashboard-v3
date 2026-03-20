"""Minimalist theme: no filled header bar, slim header, generous event spacing.

The calendar gets extra vertical room (340px vs 320px) by trimming the header
to 30px. All-day events show as bordered outlines rather than solid filled bars.
Section labels are rendered in regular weight for a lighter look.
"""
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle


def minimalist_theme() -> Theme:
    header_h = 28                         # slim header for a clean look
    bottom_h = 112                        # slightly taller bottom panels
    week_h = 480 - header_h - bottom_h    # 340px calendar
    bottom_y = header_h + week_h          # 368

    return Theme(
        name="minimalist",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, header_h),
            week_view=ComponentRegion(0, header_h, 800, week_h),
            weather=ComponentRegion(0, bottom_y, 280, bottom_h),
            birthdays=ComponentRegion(280, bottom_y, 260, bottom_h),
            info=ComponentRegion(540, bottom_y, 260, bottom_h),
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=False,        # plain text header, no filled bar
            invert_today_col=False,     # clean: no inverted today column
            invert_allday_bars=False,   # outlined bars instead of solid filled
            spacing_scale=1.3,          # generous but not excessive
            label_font_size=10,
            label_font_weight="regular",
        ),
    )
