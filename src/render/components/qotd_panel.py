"""Quote-of-the-Day panel and companion weather banner for the ``qotd`` theme.

Two independent draw functions:

    draw_qotd()         — Fills the main region with the day's quote, large and
                          centered, using the theme's decorative bold font.
    draw_qotd_weather() — Fills the banner region with a compact horizontal
                          weather summary (icon, temperature, conditions, forecast).
"""

from __future__ import annotations

from datetime import date

from PIL import ImageDraw

from src.data.models import WeatherData
from src.render.components.info_panel import _quote_for_today
from src.render.fonts import weather_icon as weather_icon_font
from src.render.icons import draw_weather_icon
from src.render.moon import moon_phase_glyph
from src.render.primitives import hline, text_height
from src.render.theme import ComponentRegion, ThemeStyle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wrap_lines(text: str, font, max_width: int) -> list[str]:
    """Word-wrap *text* into lines that each fit within *max_width* pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if font.getlength(test) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Main quote panel
# ---------------------------------------------------------------------------

def draw_qotd(
    draw: ImageDraw.ImageDraw,
    today: date,
    *,
    region: ComponentRegion | None = None,
    style: ThemeStyle | None = None,
) -> None:
    """Draw the quote of the day, typographically centered in *region*.

    Tries font sizes from large to small, picking the largest size at which
    the full quote fits vertically.  The quote text and attribution are then
    centered both horizontally and vertically within the region.
    """
    if region is None:
        region = ComponentRegion(0, 0, 800, 400)
    if style is None:
        style = ThemeStyle()

    quote = _quote_for_today(today)
    text = f'\u201c{quote["text"]}\u201d'   # "…" curly quotes
    author = f'\u2014\u2002{quote["author"]}'  # — thin-space author

    h_pad = 52   # horizontal padding from region edges
    v_pad = 28   # vertical padding at top/bottom
    max_w = region.w - h_pad * 2

    quote_font_fn = style.font_bold
    best_size = 20
    best_lines: list[str] = []
    best_quote_font = None
    best_attr_font = None

    for size in (52, 48, 44, 40, 36, 32, 28, 24, 20):
        q_font = quote_font_fn(size)
        a_size = max(13, int(size * 0.52))
        a_font = style.font_semibold(a_size)
        lines = _wrap_lines(text, q_font, max_w)
        lh = text_height(q_font)
        line_gap = max(4, size // 6)
        attr_gap = max(12, size // 3)
        attr_lh = text_height(a_font)
        total_h = (
            len(lines) * lh
            + max(0, len(lines) - 1) * line_gap
            + attr_gap
            + attr_lh
        )
        if total_h <= region.h - v_pad * 2:
            best_size = size
            best_lines = lines
            best_quote_font = q_font
            best_attr_font = a_font
            break

    # Fallback: force size 20, allow up to 8 lines
    if not best_lines:
        best_quote_font = quote_font_fn(20)
        best_attr_font = style.font_semibold(13)
        best_lines = _wrap_lines(text, best_quote_font, max_w)[:8]

    lh = text_height(best_quote_font)
    line_gap = max(4, best_size // 6)
    attr_gap = max(12, best_size // 3)
    attr_lh = text_height(best_attr_font)
    total_h = (
        len(best_lines) * lh
        + max(0, len(best_lines) - 1) * line_gap
        + attr_gap
        + attr_lh
    )

    # Start y for vertical centering
    y = region.y + (region.h - total_h) // 2

    # Draw each wrapped line, centered horizontally
    for line in best_lines:
        lw = int(best_quote_font.getlength(line))
        x = region.x + (region.w - lw) // 2
        draw.text((x, y), line, font=best_quote_font, fill=style.fg)
        y += lh + line_gap

    # Attribution — gap after last line, then centered
    y += attr_gap - line_gap
    aw = int(best_attr_font.getlength(author))
    ax = region.x + (region.w - aw) // 2
    draw.text((ax, y), author, font=best_attr_font, fill=style.fg)


# ---------------------------------------------------------------------------
# Weather banner (full-width horizontal strip)
# ---------------------------------------------------------------------------

def draw_qotd_weather(
    draw: ImageDraw.ImageDraw,
    weather: WeatherData | None,
    today: date | None = None,
    *,
    region: ComponentRegion | None = None,
    style: ThemeStyle | None = None,
) -> None:
    """Draw a compact full-width weather banner.

    Horizontal layout (left → right):
      1. Weather icon + large temperature
      2. Current description, Hi/Lo, feels-like / wind
      3. 1–3 day forecast columns
      4. Moon phase glyph (far right)

    A single thin separator line runs across the very top of the region.
    """
    if region is None:
        region = ComponentRegion(0, 400, 800, 80)
    if style is None:
        style = ThemeStyle()

    x0 = region.x
    y0 = region.y
    w = region.w
    h = region.h
    pad = 14
    center_y = y0 + h // 2

    # Thin separator between quote area and banner
    hline(draw, y0, x0, x0 + w - 1, fill=style.fg)

    if weather is None:
        msg_font = style.font_regular(13)
        msg = "Weather unavailable"
        bbox = draw.textbbox((0, 0), msg, font=msg_font)
        mw = bbox[2] - bbox[0]
        mh = bbox[3] - bbox[1]
        draw.text(
            (x0 + (w - mw) // 2, y0 + (h - mh) // 2),
            msg, font=msg_font, fill=style.fg,
        )
        return

    # ---- Section 1: icon + temperature ----
    icon_size = 40
    icon_x = x0 + pad
    icon_y = center_y - icon_size // 2
    draw_weather_icon(draw, (icon_x, icon_y), weather.current_icon, size=icon_size, fill=style.fg)

    temp_font = style.font_bold(34)
    temp_str = f"{weather.current_temp:.0f}°"
    temp_bbox = draw.textbbox((0, 0), temp_str, font=temp_font)
    temp_h = temp_bbox[3] - temp_bbox[1]
    temp_x = icon_x + icon_size + 6
    temp_y = center_y - temp_h // 2 - temp_bbox[1]
    draw.text((temp_x, temp_y), temp_str, font=temp_font, fill=style.fg)
    temp_right = temp_x + (temp_bbox[2] - temp_bbox[0])

    # ---- Section 2: description + hi/lo + detail ----
    sec2_x = temp_right + 20
    row_gap = 3

    desc_font = style.font_semibold(13)
    desc = weather.current_description.title()
    desc_bbox = draw.textbbox((0, 0), desc, font=desc_font)
    desc_h = desc_bbox[3] - desc_bbox[1]

    hilo_font = style.font_regular(12)
    hilo_str = f"H:{weather.high:.0f}°  L:{weather.low:.0f}°"
    hilo_bbox = draw.textbbox((0, 0), hilo_str, font=hilo_font)
    hilo_h = hilo_bbox[3] - hilo_bbox[1]

    detail_font = style.font_regular(11)
    detail_parts: list[str] = []
    if weather.feels_like is not None:
        detail_parts.append(f"Feels {weather.feels_like:.0f}°")
    if weather.wind_speed is not None:
        from src.fetchers.weather import deg_to_compass
        wind_str = f"Wind {weather.wind_speed:.0f}mph"
        if weather.wind_deg is not None:
            wind_str += f" {deg_to_compass(weather.wind_deg)}"
        detail_parts.append(wind_str)
    detail_str = "  ·  ".join(detail_parts) if detail_parts else f"Humidity {weather.humidity}%"
    detail_bbox = draw.textbbox((0, 0), detail_str, font=detail_font)
    detail_h = detail_bbox[3] - detail_bbox[1]

    block_h = desc_h + row_gap + hilo_h + row_gap + detail_h
    by = center_y - block_h // 2

    draw.text((sec2_x, by - desc_bbox[1]), desc, font=desc_font, fill=style.fg)
    by += desc_h + row_gap
    draw.text((sec2_x, by - hilo_bbox[1]), hilo_str, font=hilo_font, fill=style.fg)
    by += hilo_h + row_gap
    draw.text((sec2_x, by - detail_bbox[1]), detail_str, font=detail_font, fill=style.fg)

    # ---- Section 3: forecast columns ----
    # Reserve space on the right for the moon glyph
    moon_reserve = 32
    sec2_max_w = int(w * 0.32)
    sec3_x = sec2_x + sec2_max_w + 16
    sec3_right = x0 + w - pad - moon_reserve

    forecast_items = weather.forecast or []
    n_cols = min(len(forecast_items), 3)

    if n_cols > 0 and sec3_x < sec3_right:
        col_w = (sec3_right - sec3_x) // n_cols
        day_font = style.font_semibold(11)
        sm_font = style.font_regular(11)
        fc_icon_size = 18

        for i, fc in enumerate(forecast_items[:n_cols]):
            cx = sec3_x + i * col_w
            row_lh = text_height(day_font)
            block_fc_h = fc_icon_size + 2 + row_lh
            fc_y = center_y - block_fc_h // 2

            draw_weather_icon(draw, (cx, fc_y), fc.icon, size=fc_icon_size, fill=style.fg)
            tx = cx + fc_icon_size + 4
            draw.text((tx, fc_y), fc.date.strftime("%a"), font=day_font, fill=style.fg)
            draw.text(
                (tx, fc_y + row_lh + 2),
                f"{fc.high:.0f}°/{fc.low:.0f}°",
                font=sm_font, fill=style.fg,
            )

    # ---- Moon phase glyph (right edge) ----
    if today is not None:
        moon_glyph = moon_phase_glyph(today)
        moon_font = weather_icon_font(22)
        moon_bbox = draw.textbbox((0, 0), moon_glyph, font=moon_font)
        moon_w = moon_bbox[2] - moon_bbox[0]
        moon_x = x0 + w - pad - moon_w - moon_bbox[0]
        moon_y = center_y - (moon_bbox[3] - moon_bbox[1]) // 2 - moon_bbox[1]
        draw.text((moon_x, moon_y), moon_glyph, font=moon_font, fill=style.fg)
