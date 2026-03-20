"""Tests for the theme system (src/render/theme.py) and built-in themes."""

from datetime import date, datetime, timedelta

import pytest
from PIL import Image

from src.config import DisplayConfig
from src.data.models import (
    Birthday, CalendarEvent, DashboardData, DayForecast, WeatherData,
)
from src.render.canvas import render_dashboard
from src.render.theme import (
    AVAILABLE_THEMES,
    ComponentRegion,
    Theme,
    ThemeLayout,
    ThemeStyle,
    default_layout,
    default_theme,
    load_theme,
)


# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

def _make_data(today: date | None = None) -> DashboardData:
    today = today or date(2024, 3, 15)
    now = datetime.combine(today, datetime.min.time().replace(hour=8))
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    return DashboardData(
        fetched_at=now,
        events=[
            CalendarEvent(
                summary="Team Standup",
                start=datetime.combine(
                    week_start + timedelta(days=1),
                    datetime.min.time().replace(hour=9),
                ),
                end=datetime.combine(
                    week_start + timedelta(days=1),
                    datetime.min.time().replace(hour=9, minute=30),
                ),
            ),
        ],
        weather=WeatherData(
            current_temp=55.0,
            current_icon="01d",
            current_description="clear",
            high=60.0,
            low=45.0,
            humidity=50,
            forecast=[
                DayForecast(
                    date=today + timedelta(days=1), high=58.0, low=42.0,
                    icon="02d", description="partly cloudy",
                ),
            ],
        ),
        birthdays=[Birthday(name="Alice", date=today + timedelta(days=5), age=30)],
    )


# ---------------------------------------------------------------------------
# ThemeStyle
# ---------------------------------------------------------------------------

class TestThemeStyle:
    def test_default_values(self):
        s = ThemeStyle()
        assert s.fg == 0    # BLACK
        assert s.bg == 1    # WHITE
        assert s.invert_header is True
        assert s.invert_today_col is True
        assert s.invert_allday_bars is True
        assert s.spacing_scale == 1.0
        assert s.label_font_size == 12
        assert s.label_font_weight == "bold"

    def test_default_fonts_filled_by_post_init(self):
        """Leaving font callables as None triggers __post_init__ default assignment."""
        s = ThemeStyle()
        assert s.font_regular is not None
        assert s.font_medium is not None
        assert s.font_semibold is not None
        assert s.font_bold is not None

    def test_font_callables_return_font_objects(self):
        from PIL import ImageFont
        s = ThemeStyle()
        for fn in (s.font_regular, s.font_medium, s.font_semibold, s.font_bold):
            result = fn(12)
            assert isinstance(result, ImageFont.FreeTypeFont)

    def test_label_font_method_bold(self):
        from PIL import ImageFont
        s = ThemeStyle(label_font_weight="bold", label_font_size=12)
        assert isinstance(s.label_font(), ImageFont.FreeTypeFont)

    def test_label_font_method_regular(self):
        from PIL import ImageFont
        s = ThemeStyle(label_font_weight="regular", label_font_size=11)
        assert isinstance(s.label_font(), ImageFont.FreeTypeFont)

    def test_custom_fg_bg(self):
        s = ThemeStyle(fg=1, bg=0)
        assert s.fg == 1
        assert s.bg == 0


# ---------------------------------------------------------------------------
# ComponentRegion
# ---------------------------------------------------------------------------

class TestComponentRegion:
    def test_default_visible(self):
        r = ComponentRegion(0, 0, 100, 50)
        assert r.visible is True

    def test_invisible(self):
        r = ComponentRegion(0, 0, 100, 50, visible=False)
        assert r.visible is False


# ---------------------------------------------------------------------------
# ThemeLayout
# ---------------------------------------------------------------------------

class TestThemeLayout:
    def test_default_layout_canvas_size(self):
        layout = default_layout()
        assert layout.canvas_w == 800
        assert layout.canvas_h == 480

    def test_default_layout_header_region(self):
        layout = default_layout()
        assert layout.header.x == 0
        assert layout.header.y == 0
        assert layout.header.w == 800
        assert layout.header.h == 40

    def test_default_layout_week_view_region(self):
        layout = default_layout()
        assert layout.week_view.x == 0
        assert layout.week_view.y == 40
        assert layout.week_view.w == 800
        assert layout.week_view.h == 320

    def test_default_layout_bottom_panels_y(self):
        layout = default_layout()
        assert layout.weather.y == 360
        assert layout.birthdays.y == 360
        assert layout.info.y == 360

    def test_default_layout_bottom_panels_total_width(self):
        layout = default_layout()
        total = layout.weather.w + layout.birthdays.w + layout.info.w
        assert total == 800

    def test_default_draw_order(self):
        layout = default_layout()
        assert layout.draw_order == ["header", "week_view", "weather", "birthdays", "info"]

    def test_regions_cover_full_canvas(self):
        """Header + week_view + bottom row heights should sum to canvas height."""
        layout = default_layout()
        h_total = layout.header.h + layout.week_view.h + layout.weather.h
        assert h_total == layout.canvas_h


# ---------------------------------------------------------------------------
# default_theme / load_theme
# ---------------------------------------------------------------------------

class TestDefaultTheme:
    def test_returns_theme_instance(self):
        t = default_theme()
        assert isinstance(t, Theme)

    def test_name_is_default(self):
        t = default_theme()
        assert t.name == "default"

    def test_style_is_themeestyle(self):
        t = default_theme()
        assert isinstance(t.style, ThemeStyle)

    def test_layout_is_themelayout(self):
        t = default_theme()
        assert isinstance(t.layout, ThemeLayout)


class TestLoadTheme:
    def test_loads_default(self):
        t = load_theme("default")
        assert isinstance(t, Theme)
        assert t.name == "default"

    def test_loads_cyberpunk(self):
        t = load_theme("cyberpunk")
        assert isinstance(t, Theme)
        assert t.name == "cyberpunk"

    def test_loads_minimalist(self):
        t = load_theme("minimalist")
        assert isinstance(t, Theme)
        assert t.name == "minimalist"

    def test_loads_old_fashioned(self):
        t = load_theme("old_fashioned")
        assert isinstance(t, Theme)
        assert t.name == "old_fashioned"

    def test_unknown_name_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            load_theme("nonexistent_theme_xyz")

    def test_available_themes_contains_expected(self):
        assert "default" in AVAILABLE_THEMES
        assert "cyberpunk" in AVAILABLE_THEMES
        assert "minimalist" in AVAILABLE_THEMES
        assert "old_fashioned" in AVAILABLE_THEMES


# ---------------------------------------------------------------------------
# render_dashboard with themes
# ---------------------------------------------------------------------------

class TestRenderDashboardWithThemes:
    def _cfg(self) -> DisplayConfig:
        return DisplayConfig()

    def test_default_theme_produces_valid_image(self):
        data = _make_data()
        result = render_dashboard(data, self._cfg(), theme=default_theme())
        assert isinstance(result, Image.Image)
        assert result.mode == "1"
        assert result.size == (800, 480)

    def test_none_theme_defaults_to_default(self):
        data = _make_data()
        result = render_dashboard(data, self._cfg(), theme=None)
        assert isinstance(result, Image.Image)
        assert result.size == (800, 480)

    def test_cyberpunk_theme_produces_valid_image(self):
        data = _make_data()
        t = load_theme("cyberpunk")
        result = render_dashboard(data, self._cfg(), theme=t)
        assert isinstance(result, Image.Image)
        assert result.mode == "1"
        assert result.size == (800, 480)

    def test_cyberpunk_canvas_starts_black(self):
        """Cyberpunk bg=0 means the canvas background pixel is BLACK (0)."""
        data = _make_data()
        data.events = []  # minimal content so background is visible
        t = load_theme("cyberpunk")
        result = render_dashboard(data, self._cfg(), theme=t)
        # Top-left corner should be black (0) for cyberpunk (bg=0)
        assert result.getpixel((0, 0)) == 0

    def test_default_canvas_starts_white(self):
        """Default bg=1 means the canvas background is WHITE (1)."""
        data = _make_data()
        data.events = []
        t = load_theme("default")
        result = render_dashboard(data, self._cfg(), theme=t)
        # In the default theme the header is drawn immediately, so check a pixel
        # inside the body area that would be white background
        # (week body, first column, below header)
        assert result.getpixel((10, 200)) == 1  # white in body area

    def test_minimalist_theme_produces_valid_image(self):
        data = _make_data()
        t = load_theme("minimalist")
        result = render_dashboard(data, self._cfg(), theme=t)
        assert isinstance(result, Image.Image)
        assert result.mode == "1"
        assert result.size == (800, 480)

    def test_old_fashioned_theme_produces_valid_image(self):
        data = _make_data()
        t = load_theme("old_fashioned")
        result = render_dashboard(data, self._cfg(), theme=t)
        assert isinstance(result, Image.Image)
        assert result.mode == "1"
        assert result.size == (800, 480)

    def test_custom_layout_positions_components(self):
        """A theme with non-standard layout renders without crashing."""
        data = _make_data()
        custom_layout = ThemeLayout(
            canvas_w=800,
            canvas_h=480,
            header=ComponentRegion(0, 0, 800, 56),          # tall header
            week_view=ComponentRegion(0, 56, 500, 424),      # left column
            weather=ComponentRegion(500, 56, 300, 141),      # right stack
            birthdays=ComponentRegion(500, 197, 300, 141),
            info=ComponentRegion(500, 338, 300, 142),
        )
        t = Theme(name="custom", style=ThemeStyle(), layout=custom_layout)
        result = render_dashboard(data, self._cfg(), theme=t)
        assert isinstance(result, Image.Image)
        assert result.size == (800, 480)

    def test_invisible_region_skips_component(self):
        """Setting region.visible=False skips that component without crashing."""
        data = _make_data()
        layout = default_layout()
        layout.weather = ComponentRegion(
            layout.weather.x, layout.weather.y,
            layout.weather.w, layout.weather.h,
            visible=False,
        )
        t = Theme(name="no-weather", style=ThemeStyle(), layout=layout)
        result = render_dashboard(data, self._cfg(), theme=t)
        assert isinstance(result, Image.Image)


# ---------------------------------------------------------------------------
# Config wiring
# ---------------------------------------------------------------------------

class TestThemeConfigField:
    def test_config_default_theme_is_default(self):
        from src.config import Config
        cfg = Config()
        assert cfg.theme == "default"

    def test_load_config_parses_theme(self, tmp_path):
        import yaml
        from src.config import load_config
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"theme": "cyberpunk"}))
        cfg = load_config(str(config_file))
        assert cfg.theme == "cyberpunk"

    def test_unknown_theme_produces_validation_warning(self):
        from src.config import Config, validate_config
        cfg = Config()
        cfg.theme = "nonexistent_xyz"
        errors, warnings = validate_config(cfg)
        warning_fields = [w.field for w in warnings]
        assert "theme" in warning_fields

    def test_known_theme_produces_no_theme_warning(self):
        from src.config import Config, validate_config
        cfg = Config()
        cfg.theme = "cyberpunk"
        errors, warnings = validate_config(cfg)
        warning_fields = [w.field for w in warnings]
        assert "theme" not in warning_fields
