import argparse
import logging
import zoneinfo
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

from src.config import load_config, validate_config, print_validation_report
from src.data.models import (
    DashboardData, CalendarEvent, WeatherData, DayForecast, WeatherAlert, Birthday,
)
from src.fetchers.cache import load_cached_source, save_source
from src.fetchers.calendar import fetch_events, fetch_birthdays
from src.fetchers.weather import fetch_weather
from src.render.canvas import render_dashboard
from src.display.driver import DryRunDisplay, image_changed


logger = logging.getLogger(__name__)


def _resolve_tz(tz_name: str) -> tzinfo:
    """Return a tzinfo for the given IANA name, or the system local timezone for 'local'."""
    if tz_name == "local":
        return datetime.now().astimezone().tzinfo
    return zoneinfo.ZoneInfo(tz_name)


def _retry_fetch(label: str, fn):
    """Attempt fn() twice immediately to handle transient network errors."""
    try:
        return fn()
    except Exception as exc:
        logger.warning("%s failed, retrying: %s", label, exc)
    return fn()  # let the exception propagate on second failure


def _in_quiet_hours(now: datetime, start_hour: int, end_hour: int) -> bool:
    """Return True if `now` falls in the quiet window [start_hour, end_hour).

    Handles windows that cross midnight (e.g. start=23, end=6).
    """
    h = now.hour
    if start_hour > end_hour:  # crosses midnight
        return h >= start_hour or h < end_hour
    return start_hour <= h < end_hour


def _is_morning_startup(now: datetime, quiet_hours_end: int) -> bool:
    """Return True on the first 30-minute run after quiet hours end.

    Triggers a forced full refresh to start the day with a clean display.
    """
    return now.hour == quiet_hours_end and now.minute < 30


def generate_dummy_data(tz: tzinfo | None = None) -> DashboardData:
    """Create realistic dummy data for development/testing."""
    now = datetime.now(tz) if tz is not None else datetime.now()
    today = now.date()

    # Find Sunday of this week
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)

    def _at(day_offset: int, hour: int, minute: int = 0) -> datetime:
        return datetime.combine(
            week_start + timedelta(days=day_offset),
            datetime.min.time().replace(hour=hour, minute=minute),
        )

    events = [
        # Monday
        CalendarEvent(
            summary="Team Standup",
            start=_at(1, 9), end=_at(1, 9, 30),
            location="Zoom",
        ),
        CalendarEvent(
            summary="1:1 with Alex",
            start=_at(1, 14), end=_at(1, 14, 30),
            location="Conference Room B",
        ),
        # Tuesday
        CalendarEvent(
            summary="Dentist Appointment",
            start=_at(2, 10), end=_at(2, 11),
            location="123 Main St, Suite 4",
        ),
        # Wednesday–Friday: multi-day conference (spanning bar)
        CalendarEvent(
            summary="Tech Conference",
            start=datetime.combine(week_start + timedelta(days=3), datetime.min.time()),
            end=datetime.combine(week_start + timedelta(days=6), datetime.min.time()),
            is_all_day=True,
        ),
        CalendarEvent(
            summary="Yoga",
            start=_at(3, 17, 30), end=_at(3, 18, 30),
            location="Studio 12",
        ),
        # Thursday
        CalendarEvent(
            summary="Project Planning",
            start=_at(4, 10), end=_at(4, 11, 30),
        ),
        CalendarEvent(
            summary="Coffee with Sam",
            start=_at(4, 15), end=_at(4, 15, 45),
            location="Blue Bottle, Market St",
        ),
        # Friday
        CalendarEvent(
            summary="Demo Day",
            start=_at(5, 14), end=_at(5, 15),
            location="Main Auditorium",
        ),
        # Saturday
        CalendarEvent(
            summary="Farmers Market",
            start=_at(6, 9), end=_at(6, 11),
        ),
    ]

    dummy_tz = tz if tz is not None else timezone.utc
    weather = WeatherData(
        current_temp=42.0,
        current_icon="02d",
        current_description="partly cloudy",
        high=48.0,
        low=35.0,
        humidity=65,
        forecast=[
            DayForecast(
                date=today + timedelta(days=1), high=45.0, low=33.0,
                icon="10d", description="rain", precip_chance=0.80,
            ),
            DayForecast(
                date=today + timedelta(days=2), high=50.0, low=38.0,
                icon="01d", description="clear", precip_chance=0.05,
            ),
            DayForecast(
                date=today + timedelta(days=3), high=47.0, low=36.0,
                icon="04d", description="cloudy", precip_chance=0.30,
            ),
            DayForecast(
                date=today + timedelta(days=4), high=52.0, low=40.0,
                icon="02d", description="partly cloudy",
            ),
            DayForecast(
                date=today + timedelta(days=5), high=55.0, low=42.0,
                icon="09d", description="drizzle", precip_chance=0.60,
            ),
        ],
        alerts=[WeatherAlert(event="Dense Fog Advisory")],
        feels_like=38.0,
        wind_speed=12.0,
        sunrise=datetime.combine(
            today, datetime.min.time().replace(hour=6, minute=24)
        ).replace(tzinfo=dummy_tz),
        sunset=datetime.combine(
            today, datetime.min.time().replace(hour=19, minute=51)
        ).replace(tzinfo=dummy_tz),
    )

    birthdays = [
        Birthday(name="Mom", date=today + timedelta(days=3)),
        Birthday(name="Jake", date=today + timedelta(days=7), age=30),
        Birthday(name="Alice", date=today + timedelta(days=12), age=25),
        Birthday(name="Bob", date=today + timedelta(days=18)),
    ]

    return DashboardData(
        events=events, weather=weather, birthdays=birthdays,
        fetched_at=now, is_stale=False,
    )


def fetch_live_data(cfg, cache_dir: str, tz: tzinfo | None = None) -> DashboardData:
    """Fetch live data from all APIs in parallel, falling back to per-source cache on failure."""
    events: list[CalendarEvent] = []
    weather: WeatherData | None = None
    birthdays: list[Birthday] = []

    stale_sources: list[str] = []
    fetched_at = datetime.now(tz) if tz is not None else datetime.now()

    # Launch all fetchers concurrently — they are independent network calls
    with ThreadPoolExecutor(max_workers=3) as pool:
        events_future: Future = pool.submit(
            _retry_fetch, "Calendar",
            lambda: fetch_events(cfg.google, tz=tz, cache_dir=cache_dir),
        )
        weather_future: Future = pool.submit(
            _retry_fetch, "Weather",
            lambda: fetch_weather(cfg.weather, tz=tz),
        )
        birthdays_future: Future = pool.submit(
            _retry_fetch, "Birthdays",
            lambda: fetch_birthdays(cfg.google, cfg.birthdays, tz=tz),
        )

    # --- Calendar events ---
    try:
        events = events_future.result(timeout=120)
        save_source("events", events, fetched_at, cache_dir)
        logger.info("Fetched %d calendar events", len(events))
    except Exception as exc:
        logger.error("Calendar fetch failed: %s", exc)
        cached = load_cached_source("events", cache_dir)
        if cached is not None:
            events, _ = cached
            stale_sources.append("events")
            logger.warning("Using cached events")

    # --- Weather ---
    try:
        weather = weather_future.result(timeout=120)
        save_source("weather", weather, fetched_at, cache_dir)
        logger.info("Fetched weather: %.1f°", weather.current_temp)
    except Exception as exc:
        logger.error("Weather fetch failed: %s", exc)
        cached = load_cached_source("weather", cache_dir)
        if cached is not None:
            weather, _ = cached
            stale_sources.append("weather")
            logger.warning("Using cached weather")

    # --- Birthdays ---
    try:
        birthdays = birthdays_future.result(timeout=120)
        save_source("birthdays", birthdays, fetched_at, cache_dir)
        logger.info("Fetched %d upcoming birthdays", len(birthdays))
    except Exception as exc:
        logger.error("Birthday fetch failed: %s", exc)
        cached = load_cached_source("birthdays", cache_dir)
        if cached is not None:
            birthdays, _ = cached
            stale_sources.append("birthdays")
            logger.warning("Using cached birthdays")

    return DashboardData(
        events=events,
        weather=weather,
        birthdays=birthdays,
        fetched_at=fetched_at,
        is_stale=bool(stale_sources),
        stale_sources=stale_sources,
    )


def main():
    parser = argparse.ArgumentParser(description="Home Dashboard for eInk display")
    parser.add_argument(
        "--dry-run", action="store_true", help="Render to PNG instead of display",
    )
    parser.add_argument(
        "--config", default="config/config.yaml", help="Path to config file",
    )
    parser.add_argument(
        "--force-full-refresh", action="store_true", help="Force a full display refresh",
    )
    parser.add_argument(
        "--dummy", action="store_true",
        help="Use dummy data instead of fetching from APIs",
    )
    parser.add_argument(
        "--check-config", action="store_true",
        help="Validate config and exit without rendering",
    )
    args = parser.parse_args()

    # Configure logging before load_config so any import-time or config-loading
    # log records are formatted correctly (fix: logging order).
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(args.config)
    logging.getLogger().setLevel(getattr(logging, cfg.log_level, logging.INFO))

    # --- Config validation ---
    errors, warnings = validate_config(cfg, config_path=args.config)
    if args.check_config:
        print_validation_report(errors, warnings)
        raise SystemExit(1 if errors else 0)
    if errors:
        print_validation_report(errors, warnings)
        logger.error("Config has fatal errors — fix them or run with --check-config for details.")
        raise SystemExit(1)
    if warnings and not args.dummy:
        print_validation_report(errors, warnings)

    tz = _resolve_tz(cfg.timezone)
    logger.info("Using timezone: %s", tz)

    # Quiet hours — skip refresh entirely between quiet_hours_start and quiet_hours_end
    now = datetime.now(tz)
    if _in_quiet_hours(now, cfg.schedule.quiet_hours_start, cfg.schedule.quiet_hours_end):
        logger.info(
            "Quiet hours (%02d:00–%02d:00) — skipping refresh",
            cfg.schedule.quiet_hours_start,
            cfg.schedule.quiet_hours_end,
        )
        return

    # Force a full refresh on the first run of the active day (morning wake-up)
    force_full = args.force_full_refresh or _is_morning_startup(now, cfg.schedule.quiet_hours_end)
    if force_full and not args.force_full_refresh:
        logger.info("Morning startup — forcing full refresh")

    # Fetch data
    if args.dummy:
        logger.info("Using dummy data")
        data = generate_dummy_data(tz=tz)
    else:
        data = fetch_live_data(cfg, cache_dir=cfg.output_dir, tz=tz)

    # Render
    logger.info("Rendering dashboard")
    image = render_dashboard(data, cfg.display, title=cfg.title)

    # Conditional refresh — skip display update when the image hasn't changed.
    # Always write in dry-run mode (useful for dev); skip hardware refresh on
    # identical images to extend eInk display lifespan and save power.
    if args.dry_run:
        display = DryRunDisplay(output_dir=cfg.output_dir)
        display.show(image)
    elif not image_changed(image, cfg.output_dir) and not force_full:
        logger.info("Image unchanged — skipping display refresh")
    else:
        from src.display.driver import WaveshareDisplay
        display = WaveshareDisplay(
            model=cfg.display.model,
            enable_partial=cfg.display.enable_partial_refresh,
            max_partials=cfg.display.max_partials_before_full,
        )
        display.show(image, force_full=force_full)

    # Write health marker so external monitoring can detect a stuck display
    try:
        marker = Path(cfg.output_dir) / "last_success.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(datetime.now(tz).isoformat() + "\n")
    except Exception as exc:
        logger.warning("Could not write last_success.txt: %s", exc)

    logger.info("Done")


if __name__ == "__main__":
    main()
