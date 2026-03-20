"""Old Fashioned theme: newspaper front page layout.

A bold masthead header with today's schedule in a spacious list on the left
(via today_view) and weather, birthdays, and a daily quote stacked in a
right-hand sidebar column — like a broadsheet newspaper's front page.
"""
from src.render.theme import ComponentRegion, Theme, ThemeLayout, ThemeStyle


def old_fashioned_theme() -> Theme:
    header_h = 52                              # tall masthead
    body_h = 480 - header_h                    # 428px

    main_w = 500                               # left column: today's schedule
    side_x = main_w
    side_w = 800 - main_w                      # 300px right sidebar

    # Right sidebar: three stacked panels filling body_h
    weather_h = 150
    birthday_h = 140
    info_h = body_h - weather_h - birthday_h   # 138px

    return Theme(
        name="old_fashioned",
        layout=ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, header_h),
            # Week view hidden — today_view replaces it
            week_view=ComponentRegion(0, header_h, main_w, body_h, visible=False),
            today_view=ComponentRegion(0, header_h, main_w, body_h),
            weather=ComponentRegion(side_x, header_h, side_w, weather_h),
            birthdays=ComponentRegion(
                side_x, header_h + weather_h, side_w, birthday_h,
            ),
            info=ComponentRegion(
                side_x, header_h + weather_h + birthday_h, side_w, info_h,
            ),
            draw_order=[
                "header", "today_view", "weather", "birthdays", "info",
            ],
        ),
        style=ThemeStyle(
            fg=0,
            bg=1,
            invert_header=True,
            invert_today_col=True,
            invert_allday_bars=True,
            spacing_scale=1.1,           # slightly airy
            label_font_size=13,
            label_font_weight="bold",
        ),
    )
