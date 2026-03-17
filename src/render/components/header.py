from datetime import datetime
from PIL import ImageDraw

from src.render import layout as L
from src.render.fonts import semibold, regular
from src.render.primitives import filled_rect, BLACK, WHITE, text_height, text_width


def draw_header(
    draw: ImageDraw.ImageDraw,
    now: datetime,
    is_stale: bool = False,
    title: str = "Home Dashboard",
):
    y = L.HEADER_Y
    pad = L.PAD

    # Filled black header band
    filled_rect(draw, (0, 0, L.WIDTH - 1, L.HEADER_H - 1), fill=BLACK)

    # Title (left) — white text on black
    title_font = semibold(18)
    th = text_height(title_font)
    title_y = y + (L.HEADER_H - th) // 2
    draw.text((pad, title_y), title, font=title_font, fill=WHITE)

    # Last updated (right) — "Updated  Mar 15 · 9:43p"
    # When stale, prefix with "! Cached  " to signal data is from a prior run
    label_font = regular(11)
    time_font = semibold(13)
    time_str = now.strftime("%-I:%M%p").replace("AM", "a").replace("PM", "p")
    date_str = now.strftime("%b %-d")
    ts = f"{date_str}  ·  {time_str}"
    updated_label = "! Cached  " if is_stale else "Updated  "

    label_w = text_width(draw, updated_label, label_font)
    ts_w = text_width(draw, ts, time_font)
    total_w = label_w + ts_w

    label_h = text_height(label_font)
    ts_h = text_height(time_font)
    label_y = y + (L.HEADER_H - label_h) // 2 + 1
    ts_y = y + (L.HEADER_H - ts_h) // 2

    right_edge = L.WIDTH - pad
    draw.text((right_edge - total_w, label_y), updated_label, font=label_font, fill=WHITE)
    draw.text((right_edge - ts_w, ts_y), ts, font=time_font, fill=WHITE)
