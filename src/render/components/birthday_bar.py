from datetime import date
from PIL import ImageDraw

from src.data.models import Birthday
from src.render import layout as L
from src.render.fonts import semibold, medium, regular, bold
from src.render.primitives import BLACK, WHITE, hline, vline, filled_rect, draw_text_truncated

# Milestone ages rendered with extra emphasis
_MILESTONE_AGES = {18, 21, 25, 30, 40, 50, 60, 65, 70, 75, 80, 90, 100}


def draw_birthdays(draw: ImageDraw.ImageDraw, birthdays: list[Birthday], today: date):
    x0 = L.BIRTHDAY_X
    y0 = L.BIRTHDAY_Y
    w = L.BIRTHDAY_W
    h = L.BIRTHDAY_H
    pad = L.PAD

    # Top border (2px for stronger section separation)
    hline(draw, y0, x0, x0 + w)
    hline(draw, y0 + 1, x0, x0 + w)

    # Right separator
    vline(draw, x0 + w - 1, y0, y0 + h)

    # Section label
    label_font = bold(12)
    draw.text((x0 + pad, y0 + pad), "BIRTHDAYS", font=label_font, fill=BLACK)

    if not birthdays:
        empty_font = regular(12)
        draw.text((x0 + pad, y0 + 32), "No upcoming birthdays", font=empty_font, fill=BLACK)
        return

    name_font = medium(13)
    milestone_font = bold(13)
    y = y0 + 32
    max_entries = 3
    line_h = 22

    for i, bday in enumerate(birthdays[:max_entries]):
        if y + line_h > y0 + h - pad:
            break

        # Countdown label
        days_until = (bday.date.replace(year=today.year) - today).days
        if days_until < 0:
            days_until = (bday.date.replace(year=today.year + 1) - today).days
        is_today_bday = days_until == 0
        if is_today_bday:
            countdown = "Today!"
        elif days_until == 1:
            countdown = "Tomorrow"
        else:
            countdown = f"in {days_until}d"

        # Feature 6: milestone badge — append age indicator when it's a notable age
        is_milestone = bday.age is not None and bday.age in _MILESTONE_AGES
        entry = f"{countdown} — {bday.name}"
        if bday.age is not None:
            if is_milestone:
                entry += f" · {bday.age}"  # milestone: "· 30" instead of "(30)"
            else:
                entry += f" ({bday.age})"

        # Choose font: bold for milestones, medium otherwise
        font = milestone_font if is_milestone else name_font

        if is_today_bday or is_milestone:
            # Invert the entire row to celebrate the birthday or milestone
            row_rect = (x0 + pad - 1, y - 1, x0 + w - pad - 1, y + line_h - 2)
            filled_rect(draw, row_rect, fill=BLACK)
            draw.ellipse((x0 + pad, y + 5, x0 + pad + 5, y + 10), fill=WHITE)
            draw_text_truncated(draw, (x0 + pad + 12, y), entry, font, w - pad * 2 - 14, fill=WHITE)
        else:
            draw.ellipse((x0 + pad, y + 5, x0 + pad + 5, y + 10), fill=BLACK)
            draw_text_truncated(draw, (x0 + pad + 12, y), entry, font, w - pad * 2 - 14, fill=BLACK)

        y += line_h

    # Feature 5: overflow count — show how many birthdays didn't fit
    overflow = len(birthdays) - max_entries
    if overflow > 0:
        overflow_font = regular(11)
        overflow_h = 14  # approximate height for regular(11)
        if y + overflow_h <= y0 + h - pad:
            draw.text(
                (x0 + pad + 12, y), f"+{overflow} more upcoming",
                font=overflow_font, fill=BLACK,
            )
