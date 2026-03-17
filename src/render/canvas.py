from datetime import datetime
from PIL import Image, ImageDraw

from src.data.models import DashboardData
from src.config import DisplayConfig
from src.render.components import header, week_view, weather_panel, birthday_bar, info_panel

# Base resolution all layout constants are designed for.
_BASE_W = 800
_BASE_H = 480


def render_dashboard(
    data: DashboardData, config: DisplayConfig, title: str = "Home Dashboard",
) -> Image.Image:
    """Compose all components onto a 1-bit image at the configured display resolution.

    All components are drawn at the 800×480 base resolution defined in layout.py.
    If the configured display is larger, the image is scaled up to native resolution
    before being returned.
    """
    image = Image.new("1", (_BASE_W, _BASE_H), 1)  # white background
    draw = ImageDraw.Draw(image)

    now = data.fetched_at
    today = now.date() if isinstance(now, datetime) else now

    # Header
    header.draw_header(draw, now, is_stale=data.is_stale, title=title)

    # Week view (left panel) — pass forecast for per-day weather icons in headers
    week_forecast = data.weather.forecast if data.weather else None
    week_view.draw_week(
        draw, data.events, today, forecast=week_forecast, max_busy_dots=config.max_busy_dots,
    )

    # Weather (right panel, top) — pass today for moon phase calculation
    if config.show_weather:
        weather_panel.draw_weather(draw, data.weather, today=today)

    # Birthdays (right panel, middle)
    if config.show_birthdays:
        birthday_bar.draw_birthdays(draw, data.birthdays, today)

    # Quote of the day (bottom right)
    if config.show_info_panel:
        info_panel.draw_info(draw, today)

    # Scale to native display resolution when it differs from the base layout size
    if (config.width, config.height) != (_BASE_W, _BASE_H):
        image = (
            image.convert("L")
            .resize((config.width, config.height), Image.LANCZOS)
            .convert("1")
        )

    return image
