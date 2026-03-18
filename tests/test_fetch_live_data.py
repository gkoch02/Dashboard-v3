"""Tests for fetch_live_data cache fallback logic in main.py."""

import tempfile
from datetime import datetime
from unittest.mock import patch

from src.config import Config
from src.data.models import DashboardData, WeatherData, CalendarEvent, Birthday
from src.fetchers.cache import save_cache
from src.main import fetch_live_data


def _make_cached(tmpdir: str) -> DashboardData:
    """Write a minimal cache file and return the data written.

    Uses a recent timestamp (30 minutes ago) so the cached data is within
    the default TTL window and won't be discarded as expired.
    """
    from datetime import date, timedelta
    # 3 hours ago: beyond all default fetch intervals but within TTL
    # (events TTL=120min → AGING, weather TTL=60min → AGING)
    recent = datetime.now() - timedelta(hours=3)
    cached = DashboardData(
        fetched_at=recent,
        events=[
            CalendarEvent(
                summary="Cached Event",
                start=datetime(2024, 3, 14, 9, 0),
                end=datetime(2024, 3, 14, 9, 30),
            )
        ],
        weather=WeatherData(
            current_temp=55.0,
            current_icon="01d",
            current_description="clear",
            high=60.0,
            low=45.0,
            humidity=50,
        ),
        birthdays=[Birthday(name="Cached Person", date=date(2024, 3, 20))],
    )
    save_cache(cached, tmpdir)
    return cached


class TestFetchLiveData:
    def test_all_apis_succeed(self):
        cfg = Config()
        mock_events = [
            CalendarEvent(
                summary="Live Event",
                start=datetime(2024, 3, 15, 9, 0), end=datetime(2024, 3, 15, 10, 0),
            )
        ]
        mock_weather = WeatherData(
            current_temp=42.0, current_icon="02d", current_description="cloudy",
            high=48.0, low=35.0, humidity=65,
        )
        mock_birthdays = []

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.main.fetch_events", return_value=mock_events), \
                 patch("src.main.fetch_weather", return_value=mock_weather), \
                 patch("src.main.fetch_birthdays", return_value=mock_birthdays):
                data = fetch_live_data(cfg, tmpdir)

        assert not data.is_stale
        assert data.events[0].summary == "Live Event"
        assert data.weather.current_temp == 42.0

    def test_weather_failure_uses_cache(self):
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_cached(tmpdir)
            with patch("src.main.fetch_events", return_value=[]), \
                 patch("src.main.fetch_weather", side_effect=RuntimeError("API down")), \
                 patch("src.main.fetch_birthdays", return_value=[]):
                data = fetch_live_data(cfg, tmpdir)

        assert data.is_stale
        assert data.weather is not None
        assert data.weather.current_temp == 55.0

    def test_calendar_failure_uses_cache(self):
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            _make_cached(tmpdir)
            mock_weather = WeatherData(
                current_temp=42.0, current_icon="01d", current_description="clear",
                high=48.0, low=35.0, humidity=60,
            )
            with patch("src.main.fetch_events", side_effect=Exception("Auth failed")), \
                 patch("src.main.fetch_weather", return_value=mock_weather), \
                 patch("src.main.fetch_birthdays", return_value=[]):
                data = fetch_live_data(cfg, tmpdir)

        assert data.is_stale
        assert any(e.summary == "Cached Event" for e in data.events)

    def test_all_apis_fail_no_cache(self):
        cfg = Config()
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.main.fetch_events", side_effect=Exception("down")), \
                 patch("src.main.fetch_weather", side_effect=Exception("down")), \
                 patch("src.main.fetch_birthdays", side_effect=Exception("down")):
                data = fetch_live_data(cfg, tmpdir)

        # No cache available — should return empty data, not crash
        assert data.events == []
        assert data.weather is None
        assert data.birthdays == []

    def test_successful_run_writes_cache(self):
        import os
        cfg = Config()
        mock_weather = WeatherData(
            current_temp=42.0, current_icon="01d", current_description="clear",
            high=48.0, low=35.0, humidity=60,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.main.fetch_events", return_value=[]), \
                 patch("src.main.fetch_weather", return_value=mock_weather), \
                 patch("src.main.fetch_birthdays", return_value=[]):
                fetch_live_data(cfg, tmpdir)
            assert os.path.exists(os.path.join(tmpdir, "dashboard_cache.json"))
