from datetime import date

from PIL import ImageDraw

from src.data.models import WeatherData
from src.render import layout as L
from src.render.fonts import bold, regular, medium, semibold, weather_icon as weather_icon_font
from src.render.primitives import BLACK, WHITE, filled_rect, hline, text_width, vline
from src.render.icons import draw_weather_icon
from src.render.moon import moon_phase_glyph
from src.fetchers.weather import deg_to_compass


def draw_weather(draw: ImageDraw.ImageDraw, weather: WeatherData | None, today: date | None = None):
    x0 = L.WEATHER_X
    y0 = L.WEATHER_Y
    w = L.WEATHER_W
    h = L.WEATHER_H
    pad = L.PAD

    # Top border (2px for stronger section separation)
    hline(draw, y0, x0, x0 + w)
    hline(draw, y0 + 1, x0, x0 + w)

    # Right separator
    vline(draw, x0 + w - 1, y0, y0 + h)

    # Section label + moon phase icon
    label_font = semibold(12)
    draw.text((x0 + pad, y0 + pad), "WEATHER", font=label_font, fill=BLACK)

    if today is not None:
        moon_glyph = moon_phase_glyph(today)
        moon_size = 20
        moon_font = weather_icon_font(moon_size)
        # Right-justify the moon icon within the weather panel, same vertical
        # level as the "WEATHER" label.
        label_bbox = draw.textbbox((0, 0), "WEATHER", font=label_font)
        label_mid_y = y0 + pad + label_bbox[1] + (label_bbox[3] - label_bbox[1]) // 2
        moon_bbox = draw.textbbox((0, 0), moon_glyph, font=moon_font)
        moon_glyph_w = moon_bbox[2] - moon_bbox[0]
        moon_y = label_mid_y - (moon_bbox[3] - moon_bbox[1]) // 2 - moon_bbox[1]
        moon_x = x0 + w - pad - moon_glyph_w - moon_bbox[0] - 2  # 2px inside right separator
        draw.text((moon_x, moon_y), moon_glyph, font=moon_font, fill=BLACK)

    if weather is None:
        msg_font = regular(13)
        msg = "Unavailable"
        bbox = draw.textbbox((0, 0), msg, font=msg_font)
        mw = bbox[2] - bbox[0]
        mh = bbox[3] - bbox[1]
        draw.text((x0 + (w - mw) // 2, y0 + (h - mh) // 2), msg, font=msg_font, fill=BLACK)
        return

    # Weather icon (left side) — extra left pad to avoid clipping
    icon_x = x0 + L.WEATHER_ICON_X_OFFSET
    icon_y = y0 + L.WEATHER_CONTENT_Y_OFFSET
    draw_weather_icon(draw, (icon_x, icon_y), weather.current_icon, size=40)

    # Temperature (big) — right of icon
    temp_font = bold(36)
    temp_str = f"{weather.current_temp:.0f}°"
    draw.text((x0 + L.WEATHER_TEMP_X_OFFSET, icon_y - 2), temp_str, font=temp_font, fill=BLACK)

    # Right-column detail rows
    right_x = x0 + L.WEATHER_DETAIL_X_OFFSET

    # Row 1: description
    desc_font = medium(13)
    draw.text(
        (right_x, y0 + L.WEATHER_CONTENT_Y_OFFSET),
        weather.current_description.title(), font=desc_font, fill=BLACK,
    )

    # Row 2: hi/lo + UV index when available
    hilo_font = medium(12)
    hilo_str = f"H:{weather.high:.0f}°  L:{weather.low:.0f}°"
    if weather.uv_index is not None:
        uv_suffix = f"  UV:{weather.uv_index:.0f}"
        max_detail_w = w - L.WEATHER_DETAIL_X_OFFSET - pad
        if text_width(draw, hilo_str + uv_suffix, hilo_font) <= max_detail_w:
            hilo_str += uv_suffix
    draw.text((right_x, y0 + L.WEATHER_HILO_Y_OFFSET), hilo_str, font=hilo_font, fill=BLACK)

    # Row 3: feels-like + wind speed (Feature 1)
    detail3_font = regular(11)
    detail3_parts: list[str] = []
    if weather.feels_like is not None:
        detail3_parts.append(f"Feels {weather.feels_like:.0f}°")
    if weather.wind_speed is not None:
        wind_str = f"Wind {weather.wind_speed:.0f}mph"
        if weather.wind_deg is not None:
            wind_str += f" {deg_to_compass(weather.wind_deg)}"
        detail3_parts.append(wind_str)
    if detail3_parts:
        draw.text(
            (right_x, y0 + L.WEATHER_DETAIL3_Y_OFFSET),
            "  ·  ".join(detail3_parts), font=detail3_font, fill=BLACK,
        )
    else:
        # Fall back to humidity when neither feels-like nor wind is available
        draw.text(
            (right_x, y0 + L.WEATHER_DETAIL3_Y_OFFSET),
            f"{weather.humidity}% humidity", font=detail3_font, fill=BLACK,
        )

    # Row 4: sunrise / sunset (Feature 3)
    if weather.sunrise is not None or weather.sunset is not None:
        sun_parts: list[str] = []
        if weather.sunrise is not None:
            sun_parts.append(f"↑{_fmt_time(weather.sunrise)}")
        if weather.sunset is not None:
            sun_parts.append(f"↓{_fmt_time(weather.sunset)}")
        draw.text(
            (right_x, y0 + L.WEATHER_DETAIL4_Y_OFFSET),
            "  ".join(sun_parts), font=detail3_font, fill=BLACK,
        )

    # Forecast strip along the bottom.
    # Feature 4: when 2+ alerts are active, show both as stacked compact bars in
    # the first two columns; otherwise a single alert takes the first column.
    forecast_top = y0 + h - L.WEATHER_FORECAST_H
    hline(draw, forecast_top, x0, x0 + w)

    forecast_items = weather.forecast or []
    n_alerts = len(weather.alerts)

    if n_alerts >= 2:
        # Two alert columns + up to 1 forecast column
        n_forecast_cols = min(len(forecast_items), 1)
        n_cols = 2 + n_forecast_cols
    elif n_alerts == 1:
        # One alert column + up to 2 forecast columns
        n_forecast_cols = min(len(forecast_items), 2)
        n_cols = 1 + n_forecast_cols
    else:
        n_cols = min(len(forecast_items), 3)

    if n_cols == 0:
        return

    col_w = w // n_cols
    day_font = semibold(11)
    hilo_sm_font = regular(11)
    icon_size = 18
    forecast_idx = 0

    for i in range(n_cols):
        cx = x0 + i * col_w

        if n_alerts >= 2 and i < 2:
            # Two alert columns
            _draw_alert_column(
                draw, weather.alerts[i].event, cx, forecast_top, col_w, L.WEATHER_FORECAST_H,
            )
        elif n_alerts == 1 and i == 0:
            # Single alert column
            _draw_alert_column(
                draw, weather.alerts[0].event, cx, forecast_top, col_w, L.WEATHER_FORECAST_H,
            )
        else:
            if forecast_idx < len(forecast_items):
                fc = forecast_items[forecast_idx]
                forecast_idx += 1
                fx = cx + pad
                draw_weather_icon(draw, (fx, forecast_top + 2), fc.icon, size=icon_size, fill=BLACK)
                text_x = fx + icon_size + 8
                draw.text(
                    (text_x, forecast_top + 2),
                    fc.date.strftime("%a"), font=day_font, fill=BLACK,
                )
                draw.text(
                    (text_x, forecast_top + 14),
                    f"{fc.high:.0f}°/{fc.low:.0f}°", font=hilo_sm_font, fill=BLACK,
                )
                # Feature 2: precipitation probability (only when ≥ 5%)
                if fc.precip_chance is not None and fc.precip_chance >= 0.05:
                    precip_font = regular(10)
                    draw.text(
                        (text_x, forecast_top + 25),
                        f"{fc.precip_chance:.0%}", font=precip_font, fill=BLACK,
                    )

        # Column separators
        if i < n_cols - 1:
            vline(draw, cx + col_w, forecast_top, y0 + h)


def _fmt_time(dt) -> str:
    """Format a datetime as a compact am/pm string, e.g. '6:24a'."""
    s = dt.strftime("%-I:%M%p").lower().replace(":00", "")
    return s.replace("am", "a").replace("pm", "p")


def _draw_alert_column(
    draw: ImageDraw.ImageDraw,
    alert_event: str,
    cx: int,
    top: int,
    col_w: int,
    col_h: int,
) -> None:
    """Draw an inverted alert bar filling one forecast column."""
    filled_rect(draw, (cx, top, cx + col_w - 1, top + col_h - 1), fill=BLACK)

    alert_font = semibold(10)
    label = f"! {alert_event}"
    max_w = col_w - L.PAD * 2

    # Word-wrap into up to 2 lines
    words = label.split()
    lines: list[str] = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if text_width(draw, test, alert_font) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:2]

    # Truncate last line if needed
    for i, line in enumerate(lines):
        if text_width(draw, line, alert_font) > max_w:
            while line and text_width(draw, line + "...", alert_font) > max_w:
                line = line[:-1]
            lines[i] = line + "..."

    line_h = draw.textbbox((0, 0), "Ag", font=alert_font)
    lh = line_h[3] - line_h[1]
    total_h = lh * len(lines) + (len(lines) - 1) * 2
    ty = top + (col_h - total_h) // 2

    for line in lines:
        lw = text_width(draw, line, alert_font)
        tx = cx + (col_w - lw) // 2
        draw.text((tx, ty), line, font=alert_font, fill=WHITE)
        ty += lh + 2
