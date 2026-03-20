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
    cal_w = 530                           # ~66% of 800 — wider than before for readability
    right_x = cal_w
    right_w = 800 - cal_w                 # 270px right column
    header_h = 50                         # tall decorative header
    body_h = 480 - header_h               # 430px
    # Stack three panels in the right column with proportional heights
    weather_h = 150
    birthday_h = 140
    info_h = body_h - weather_h - birthday_h  # 140px

    return Theme(
        name="old_fashioned",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, header_h),
            week_view=ComponentRegion(0, header_h, cal_w, body_h),
            weather=ComponentRegion(right_x, header_h, right_w, weather_h),
            birthdays=ComponentRegion(
                right_x, header_h + weather_h, right_w, birthday_h,
            ),
            info=ComponentRegion(
                right_x, header_h + weather_h + birthday_h, right_w, info_h,
            ),
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=True,
            invert_today_col=True,
            invert_allday_bars=True,
            spacing_scale=1.0,
            label_font_size=12,
            label_font_weight="bold",
        ),
    )
