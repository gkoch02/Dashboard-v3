# CLAUDE.md — AI Assistant Guide for Dashboard

This file provides context for AI assistants (Claude, etc.) working in this repository.

---

## Project Overview

A Python-based **eInk dashboard** for Raspberry Pi that renders calendar events, weather
forecasts, birthdays, and inspirational quotes to a supported Waveshare eInk display
(black & white). All four implementation phases plus v2 and v3 features are complete and the
application is production-ready. Multiple display sizes are supported via the
`WAVESHARE_MODELS` registry in `display/driver.py`.

**v2 features** (shipped): event location display, weather alerts (OWM OneCall), per-day
busy-ness heatmap dots, per-source cache staleness tracking, and incremental Google Calendar
sync via sync tokens.

**v3 features** (shipped): parallel fetcher execution, conditional display refresh via image
diffing, extended 6-day weather forecast with per-column forecast icons in the week view,
moon phase display in the weather panel, and multi-day spanning event bars.

---

## Repository Structure

```
Dashboard/
├── config/
│   ├── config.example.yaml   # Configuration template — copy to config.yaml, never commit the real one
│   └── quotes.json           # Optional daily-quote pool
├── credentials/              # Git-ignored — Google service account JSON lives here
├── fonts/                    # Bundled TTF fonts (Inter, Plus Jakarta Sans, Weather Icons)
├── output/                   # Mostly git-ignored — dry-run PNGs and logs written here
│   └── latest.png            # Tracked exception: latest dry-run preview
├── src/
│   ├── main.py               # CLI entry point (argparse)
│   ├── config.py             # YAML → dataclass config loader
│   ├── data/
│   │   └── models.py         # Pure dataclasses: CalendarEvent (+ event_id, location), WeatherData (+ alerts), WeatherAlert, Birthday, DashboardData (+ stale_sources)
│   ├── display/
│   │   ├── driver.py         # Abstract DisplayDriver; DryRunDisplay & WaveshareDisplay; WAVESHARE_MODELS registry; image_changed() conditional refresh
│   │   └── refresh_tracker.py# Partial-vs-full refresh state, persisted to /tmp/
│   ├── fetchers/
│   │   ├── weather.py        # OpenWeatherMap (conditions, extended forecast, alerts via OneCall 2.5)
│   │   ├── calendar.py       # Google Calendar + incremental sync (sync tokens) + birthday parsing
│   │   └── cache.py          # Per-source v2 JSON cache; save_source/load_cached_source; v1 compat
│   └── render/
│       ├── canvas.py         # render_dashboard() — top-level orchestrator
│       ├── layout.py         # All pixel constants (widths, heights, margins)
│       ├── fonts.py          # Font loader with @lru_cache
│       ├── icons.py          # OWM icon-code → weather-icon character map
│       ├── moon.py           # Pure-math moon phase calculator (synodic month); moon_phase_glyph()
│       ├── primitives.py     # Shared draw helpers (truncated text, wrapped text)
│       └── components/       # One file per UI region
│           ├── header.py
│           ├── week_view.py
│           ├── weather_panel.py
│           ├── birthday_bar.py
│           └── info_panel.py
├── Makefile                  # Primary task runner (see below)
├── requirements.txt          # Core Python deps
└── requirements-pi.txt       # Raspberry Pi hardware deps (RPi.GPIO, spidev)
```

---

## Development Workflow

### Setup

```bash
make setup       # Creates venv/ and installs requirements.txt
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your API keys and settings
```

### Common Tasks

| Command | What it does |
|---|---|
| `make dry` | Render a PNG with dummy data → `output/latest.png` |
| `make test` | Run `pytest tests/ -v` |
| `make deploy` | rsync project to Raspberry Pi (requires SSH config) |
| `make install` | Copy systemd timer/service to Pi and enable the timer |

### Running Manually

```bash
python src/main.py --dry-run --dummy          # Offline render with dummy data, no hardware needed
python src/main.py --dry-run                  # Live data → local PNG only (no display hardware)
python src/main.py --dry-run --config path/to/config.yaml
python src/main.py --force-full-refresh       # Force full eInk refresh cycle
```

`--dry-run` without `--dummy` fetches live data from Google Calendar, OpenWeatherMap, etc.
and renders the result to `output/latest.png` without requiring eInk display hardware.
This is the easiest way to preview what the dashboard will look like with real data.

---

## Architecture Conventions

### Layered Architecture

```
CLI (main.py)
  └── Config loading (config.py)
  └── Data models (data/models.py)            ← pure dataclasses, no I/O
  └── Rendering (render/canvas.py)            ← pure Pillow, no I/O
        └── Components (render/components/)
        └── Primitives (render/primitives.py)
  └── Display drivers (display/driver.py)     ← hardware abstraction
```

- **Data models are pure.** `DashboardData` and friends are simple dataclasses with no
  methods that touch files, networks, or hardware.
- **Rendering is pure.** `render_dashboard()` takes data and config, returns a `PIL.Image`.
  It never reads files or calls APIs.
- **Side effects are isolated** to `main.py` (orchestration), `display/driver.py` (hardware),
  and `refresh_tracker.py` (filesystem state).

### Component Pattern

Each UI region lives in `render/components/<name>.py` and exposes a single `draw_*()` function:

```python
def draw_header(draw: ImageDraw.ImageDraw, data: DashboardData, config: Config) -> None:
    ...
```

Components receive an `ImageDraw` object, relevant data, and config. They never create
images themselves — the canvas owns the image.

### Layout Constants

All pixel geometry is centralised in `render/layout.py`. **Do not hard-code pixel values
inside components.** Import from `layout` instead.

The file is organised into sections: canvas dimensions, region origins/sizes, week-view
internals (`WEEK_COL_W`, `WEEK_LAST_COL_W`), weather panel internals
(`WEATHER_ICON_X_OFFSET`, `WEATHER_TEMP_X_OFFSET`, `WEATHER_DETAIL_X_OFFSET`,
`WEATHER_CONTENT_Y_OFFSET`, `WEATHER_FORECAST_H`, `WEATHER_ALERT_H`), and shared padding
constants.

All layout constants are defined at the **800 × 480 base resolution**. `render_dashboard()`
renders at this size and then scales to the configured display resolution via LANCZOS
resampling (in `canvas.py`) — components never need to know the target display size.

```
┌────────────────────── 800 ──────────────────────────┐
│  Header                              (height: 40)   │
│─────────────────────────────────────────────────────│
│  Week view (7-day calendar grid)    (height: 320)   │
│─────────────────────────────────────────────────────│
│  Weather  │  Birthdays  │  Info panel (height: 120) │
└────────────────────────────────────────────────────-┘
```

### eInk-Specific Rules

- Always render a **1-bit image** (`mode="1"` or convert before displaying).
- Partial refreshes degrade display quality over time. `RefreshTracker` enforces a
  configurable full-refresh cycle — do not bypass it.
- Hardware imports (`waveshare_epd`, `RPi.GPIO`, `spidev`) must be **lazy** (imported
  inside the `WaveshareDisplay` class/methods) so the codebase runs on non-Pi machines.
- `WaveshareDisplay` uses `importlib.import_module()` to load the correct per-model driver
  at runtime. The model is looked up in `WAVESHARE_MODELS` in `display/driver.py`; adding a
  new display only requires a new entry there.

### Configuration

- Config lives in `config/config.yaml` (git-ignored). Use `config/config.example.yaml` as
  the source-of-truth template.
- The `Config` dataclass in `config.py` provides typed defaults. YAML fields are optional;
  missing fields fall back to defaults — do not break this behaviour.
- `display.model` selects the Waveshare driver and auto-derives `display.width` /
  `display.height` from `WAVESHARE_MODELS` in `load_config()`. Explicit `width`/`height`
  in YAML override the model defaults.
- `display.max_partials_before_full` (default `6`) controls how many partial eInk refreshes
  are allowed before the next write is forced full. The value flows from config →
  `WaveshareDisplay(max_partials=...)` → `RefreshTracker.load(max_partials=...)`.
- `timezone` is a top-level IANA timezone name (e.g. `"America/Los_Angeles"`) or `"local"`
  (default) to follow the system clock. It is resolved once in `main.py` via `_resolve_tz()`
  and threaded through all fetchers and `generate_dummy_data` so that `date.today()` /
  `datetime.now()` consistently reflect the configured location rather than the server clock.
- `schedule.quiet_hours_start` / `schedule.quiet_hours_end` (defaults `23` / `6`) define the
  overnight quiet window. `ScheduleConfig` lives in `config.py`. `main.py` checks
  `_in_quiet_hours()` immediately after resolving the timezone and returns early if the
  current time falls in the window. The first run each morning (`_is_morning_startup()`)
  forces a full eInk refresh.
- `title` is a top-level string (default `"Home Dashboard"`) displayed in the header bar.
  Set `title: "My Dashboard"` in `config.yaml` to customise it.
- `google.contacts_email` is required when `birthdays.source` is `"contacts"`. The service
  account must have domain-wide delegation enabled in Google Workspace Admin with the
  `contacts.readonly` scope granted. `_build_people_service()` in `fetchers/calendar.py`
  calls `.with_subject(contacts_email)` to impersonate that user.
- Never commit `config/config.yaml`, `credentials/`, or any file containing API keys.

### Per-Source Cache (v2)

`fetchers/cache.py` stores data in a single JSON file (`output/dashboard_cache.json`) with
per-source buckets so each data source can fail and recover independently:

```json
{
  "schema_version": 2,
  "events":    {"fetched_at": "2026-03-16T08:00:00", "data": [...]},
  "weather":   {"fetched_at": "2026-03-16T08:00:00", "data": {...}},
  "birthdays": {"fetched_at": "2026-03-16T08:00:00", "data": [...]}
}
```

- `save_source(source, data, fetched_at, cache_dir)` — writes one bucket without touching others.
- `load_cached_source(source, cache_dir)` — returns `(data, fetched_at)` or `None`.
- v1 files (no `schema_version`) are transparently migrated via `_deserialise_v1()`.
- `DashboardData.stale_sources: list[str]` lists which sources came from cache (e.g. `["weather"]`).

### Incremental Calendar Sync

After the first full sync, `fetchers/calendar.py` stores a `nextSyncToken` per calendar in
`output/calendar_sync_state.json`. Subsequent calls use that token instead of `timeMin`/`timeMax`
to download only changed events, greatly reducing API quota usage.

Key functions:
- `_fetch_full()` — paginates all events and captures the `nextSyncToken` from the last page.
- `_fetch_incremental()` — uses the stored token; returns `needs_reset=True` on HTTP 410 Gone.
- `_apply_delta()` — merges add/update/cancel items into the stored event list by `event_id`.
- `_filter_to_window()` — filters the merged store to the current display week client-side.

`CalendarEvent.event_id` (optional `str`) holds the Google event ID used for delta merging.

### Weather Alerts

`fetchers/weather.py` makes a best-effort call to the OWM OneCall 2.5 endpoint
(`/data/2.5/onecall?exclude=minutely,hourly,daily,current`) after the main weather fetch.
Any failure silently returns `[]` — alerts are non-critical.

`WeatherData.alerts: list[WeatherAlert]` holds the results. `WeatherAlert.event` is the
short NWS/WMO alert name (e.g. `"Dense Fog Advisory"`).

In `weather_panel.py`, alerts occupy columns in the **forecast strip** (the bottom
`WEATHER_FORECAST_H = 38px` row), not the humidity row. The column allocation is:

- 0 alerts → 3 forecast columns
- 1 alert  → 1 alert column + up to 2 forecast columns
- 2+ alerts → 2 alert columns + up to 1 forecast column

Each alert column is rendered by `_draw_alert_column()` as a filled black rectangle with
`"! {event}"` text word-wrapped to up to 2 lines and centred in white (`semibold(10)`).
(`WEATHER_ALERT_H = 15` in `layout.py` is a legacy constant no longer used.)

### Parallel Fetcher Execution (v3)

`fetch_live_data()` in `main.py` uses `concurrent.futures.ThreadPoolExecutor(max_workers=3)`
to run calendar, weather, and birthday fetchers concurrently. All three are independent
network calls; running them in parallel cuts refresh latency roughly in half. Cache fallback
per source still works — each future's result is collected individually.

### Conditional Display Refresh (v3)

`display/driver.py` exposes `image_changed(image, output_dir)` which computes a SHA-256
hash of the raw pixel bytes and compares it against the previously persisted hash in
`<output_dir>/last_image_hash.txt`. When the image is unchanged (common overnight or on
quiet days), `main.py` skips the eInk refresh entirely. This extends display lifespan and
saves power on battery-powered Pi setups. `--force-full-refresh` bypasses this check.
Dry-run mode always writes output regardless.

### Refresh Schedule

The production schedule is driven by `deploy/dashboard.timer` (systemd) firing at `:00` and
`:30` of every hour. All scheduling logic lives in `main.py` — the timer runs 24/7 and lets
the app decide:

1. **Quiet hours** — `_in_quiet_hours(now, start, end)` checks whether the current local
   time falls in `[quiet_hours_start, quiet_hours_end)`, handling windows that cross midnight.
   If true, `main.py` logs and returns immediately — no fetch, no render, no display write.
2. **Morning full refresh** — `_is_morning_startup(now, quiet_hours_end)` returns `True`
   when `now.hour == quiet_hours_end and now.minute < 30` (the first 30-minute slot after
   quiet ends). `main.py` sets `force_full = True` for that run.
3. **Partial vs. full** — on all other runs, `RefreshTracker` tracks the partial-refresh
   count and triggers a full refresh every `max_partials_before_full` actual display writes
   (default 6, ~3 hours at 30-minute polling).

`--force-full-refresh` on the CLI always wins and bypasses all three checks above.

### Moon Phase (v3)

`render/moon.py` computes the moon's phase using the synodic month length (29.53059 days)
and a known new-moon reference date (2000-01-06 18:14 UTC). No external API is needed.

Key functions:
- `moon_phase_age(date)` — returns age in days (0 = new moon, ~14.76 = full moon).
- `moon_phase_name(date)` — returns one of 8 human-readable phase names.
- `moon_phase_glyph(date)` — returns a Weather Icons font character (28 distinct glyphs).

The glyph is rendered in `weather_panel.py` next to the "WEATHER" section label at size 20,
vertically centred using the actual glyph bbox (icon fonts have oversized internal bounding
boxes — never rely on font metrics alone for positioning).

### Multi-Day Spanning Event Bars (v3)

All-day events spanning 2+ calendar days are rendered as continuous black bars across
multiple week-view columns instead of being repeated as per-day bars.

Key functions in `week_view.py`:
- `_is_multiday(event)` — True when event is all-day and spans ≥ 2 days.
- `_collect_spanning_events(events, week_start, week_end)` — returns `(event, first_col,
  last_col)` tuples, clamped to the visible week.
- Spanning bars are drawn at the top of the body area before per-column content. Per-day
  events are offset below by `span_total_h`. Spanning events are excluded from per-day
  rendering via an identity set (`spanning_ids`).

### Extended Weather Forecast (v3)

`fetchers/weather.py` now returns up to **6 days** of forecast data (was 3) from the OWM
5-day/3-hour endpoint. The weather panel bottom strip still shows up to 3 forecast columns
(fewer when alerts are present — see Weather Alerts above), but **small forecast icons are
rendered in week-view column headers** for all days that have forecast data. `draw_week()`
accepts an optional `forecast: list[DayForecast]` parameter; `canvas.py` passes
`data.weather.forecast` through.

Each forecast column in the strip shows a weather icon (18px), the abbreviated day name
(`semibold(11)`), the high/low temps (`regular(11)`), and — when `DayForecast.precip_chance
≥ 5%` — a precipitation probability percentage on a third line (`regular(10)`). All three
text rows fit within the `WEATHER_FORECAST_H = 38px` strip at offsets +2, +14, and +25.

### Fonts

- Fonts are loaded with `@lru_cache` in `render/fonts.py`. Always use the loader; never
  open font files directly.
- **Plus Jakarta Sans** — primary UI font (header, section labels, timestamps, weather
  details). Fallback: **Inter**.
- **Fraunces Bold** — display serif for the large weekend day number and month label.
  Loaded as a variable font; `_get_variable_font()` sets `wght=700` via
  `set_variation_by_axes()`.
- **Barlow Condensed** (Medium, SemiBold) — condensed sans for event titles and all-day
  event bars in the week view. Use SemiBold for white-on-black (inverted) bars.
- **Lora Italic** — editorial serif for the quote body in the info panel.
- **weathericons-regular.ttf** — icon font; use character codes from `render/icons.py`.

When adding a font that requires axis selection (variable font), use
`_get_variable_font(name, size, wght)` rather than `get_font()`. Both are `@lru_cache`d.

### Quote Selection

Quotes are selected deterministically by hashing the current date, so the same quote
appears all day. If `config/quotes.json` is absent, built-in defaults are used. Preserve
this deterministic behaviour.

The `config/quotes.json` pool (86 entries) favours sci-fi, science, philosophy, and wit —
authors include Feynman, Sagan, Adams, Herbert, Clarke, Nietzsche, Camus, Wittgenstein,
Wilde, Twain, and others. Each entry is `{"text": "...", "author": "..."}`.

---

## Code Style

- **Python 3.9+** — use built-in generics (`list[str]`, `dict[str, int]`) and `|` unions.
- **Type hints everywhere** — all function signatures must be fully annotated.
- **Dataclasses** for data objects; avoid plain dicts for structured data.
- `snake_case` for functions and variables; `PascalCase` for classes.
- **Linting** — the codebase is clean under `flake8 src/ tests/ --max-line-length=100`. No
  formatter is configured; follow PEP 8 and keep lines ≤ 100 characters. There is no `make lint`
  target yet — run flake8 manually before committing.

---

## Key Files to Read Before Changing Things

| Changing… | Read first |
|---|---|
| Any component layout | `render/layout.py` |
| Rendering pipeline | `render/canvas.py` |
| Config schema | `src/config.py` + `config/config.example.yaml` |
| Display output / conditional refresh | `display/driver.py` |
| Partial vs. full refresh tracking | `display/refresh_tracker.py` |
| Quiet hours / morning startup / schedule | `src/main.py` (`_in_quiet_hours`, `_is_morning_startup`) |
| Data shapes | `data/models.py` |
| Entry-point flags / fetcher orchestration | `src/main.py` |
| Moon phase calculation | `render/moon.py` |
| Multi-day event spanning | `render/components/week_view.py` (`_collect_spanning_events`) |

---

## Implemented Phases

- **Phase 1** — Rendering scaffold with dummy data (complete)
- **Phase 2** — Google Calendar integration via `google-api-python-client` (complete)
- **Phase 3** — OpenWeatherMap integration via `requests` (complete)
- **Phase 4** — Birthday parsing from local JSON file, Google Calendar events, or Google Contacts (People API) (complete)
- **v2 features** — Event location display; weather alerts (OWM OneCall 2.5); per-day
  busy-ness heatmap dots in column headers; per-source independent cache staleness with
  `stale_sources` tracking; incremental Google Calendar sync via `nextSyncToken` with
  delta merging and 410 Gone reset (complete)
- **v3 features** — Parallel fetcher execution via `ThreadPoolExecutor`; conditional
  display refresh via SHA-256 image diffing; extended 6-day weather forecast with
  per-column forecast icons in week-view headers; pure-math moon phase display in
  weather panel; multi-day spanning event bars across week-view columns (complete)
- **Refresh schedule** — configurable quiet hours (default 11 pm–6 am) with early exit in
  `main.py`; forced full refresh on morning wake-up; `max_partials_before_full` wired from
  config through to `RefreshTracker`; systemd timer switched to `OnCalendar` for
  wall-clock-aligned 30-minute firing (complete)

The `--dummy` flag remains functional for offline development and testing.

---

## Testing

```bash
make test          # pytest tests/ -v
```

Seventeen test files live in `tests/` (379 tests total):

| File | What it covers |
|---|---|
| `test_cache.py` | Cache serialisation round-trips, error paths, v1/v2 format compat |
| `test_calendar_fetcher.py` | Birthday/event parsing, `fetch_birthdays()`, `_parse_contact_birthday()`, contacts pagination, `_fetch_full`/`_fetch_incremental` pagination and errors, `_filter_to_window` edge cases, `fetch_events` incremental sync |
| `test_weather_fetcher.py` | `fetch_weather()`, `_pick_midday()`, extended forecast limit |
| `test_fetch_live_data.py` | `fetch_live_data()` — success, failure, cache fallback |
| `test_rendering.py` | `render_dashboard()` pipeline smoke tests, display scaling |
| `test_config.py` | `load_config()` — defaults, partial YAML, model auto-dimensions, `ScheduleConfig` |
| `test_config_validation.py` | `validate_config()`, `print_validation_report()` — errors, warnings, hints |
| `test_refresh_tracker.py` | `RefreshTracker` state logic, save/load round-trip |
| `test_primitives.py` | Text truncation/wrapping, drawing helpers, ellipsis-only edge case |
| `test_week_view.py` | `_fmt_time`, `_events_for_day` filtering/sorting, `draw_week` |
| `test_info_panel.py` | `_quote_for_today` determinism and fallback, `draw_info` |
| `test_display_driver.py` | `DryRunDisplay`, `WAVESHARE_MODELS` registry, `WaveshareDisplay` init/show/clear, `image_changed` |
| `test_main_utils.py` | `_retry_fetch` retry logic, `generate_dummy_data`, `_in_quiet_hours`, `_is_morning_startup` |
| `test_birthday_bar.py` | `draw_birthdays()` — today/tomorrow/milestone/overflow/non-milestone age rendering |
| `test_weather_panel.py` | `draw_weather()` — all branch paths: alerts, forecasts, precip, sunrise/sunset, `_fmt_time` |
| `test_fonts.py` | All font accessor functions in `render/fonts.py` |
| `test_v2_features.py` | v2 features: alerts, busy dots, location display, per-source cache, incremental sync |
| `test_v3_features.py` | v3 features: image diffing, parallel fetchers, moon phase, spanning events, forecast icons, full pipeline |

Use `--dummy` mode and `DryRunDisplay` to test rendering without hardware or live APIs.

---

## Deployment

The production environment is a **Raspberry Pi**. Set `display.model` in `config/config.yaml`
to match the physical display (see `WAVESHARE_MODELS` in `display/driver.py` for supported
models and their native resolutions).

```bash
make deploy        # rsync to Pi (configure SSH target in Makefile)
make install       # copy deploy/dashboard.{service,timer} to Pi and enable the timer
```

Hardware-specific dependencies are in `requirements-pi.txt`. Install them only on the Pi.
The application is driven by `deploy/dashboard.timer` (systemd), which fires at `:00` and
`:30` of every hour. All quiet-hours and morning-refresh logic lives in `main.py` — the
timer itself runs 24/7 and the app exits early during the quiet window.
