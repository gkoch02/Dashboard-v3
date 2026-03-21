# CLAUDE.md — Dashboard-v3

## Project Overview

Python eInk dashboard for Raspberry Pi. Displays a weekly calendar (Google Calendar), weather (OpenWeatherMap), upcoming birthdays, and a daily quote. Renders to a Waveshare eInk display or PNG preview. No web framework — pure CLI application.

## Quick Commands

```bash
make setup          # Create venv, install deps, copy config template
make test           # Run pytest (591 tests across 25 files)
make dry            # Preview with dummy data → output/latest.png
make check          # Validate config/config.yaml
make deploy         # Rsync to Pi
make install        # Install systemd timer on Pi
flake8 src/ tests/ --max-line-length=100   # Lint
```

## Tech Stack

- **Python 3.9+** — no async, no web framework
- **Pillow** — image rendering (PIL)
- **google-api-python-client / google-auth** — Google Calendar & Contacts APIs
- **requests** — OpenWeatherMap API
- **PyYAML** — config parsing
- **pytest** — testing (with unittest.mock)
- **flake8** — linting (max line length: 100)

## Repository Structure

```
src/
├── main.py                    # CLI entry point + orchestration
├── config.py                  # YAML → typed dataclasses
├── filters.py                 # Event filtering (calendar, keyword, all-day)
├── data/models.py             # Pure dataclasses (CalendarEvent, WeatherData, Birthday, DashboardData)
├── display/
│   ├── driver.py              # DisplayDriver ABC → DryRunDisplay, WaveshareDisplay
│   └── refresh_tracker.py     # Partial vs full refresh state machine
├── fetchers/
│   ├── calendar.py            # Google Calendar API + incremental sync + birthdays
│   ├── weather.py             # OpenWeatherMap (current + forecast + alerts)
│   ├── cache.py               # Multi-source JSON cache with per-source TTL
│   ├── circuit_breaker.py     # Per-source circuit breaker
│   └── quota_tracker.py       # Daily API call counter
└── render/
    ├── canvas.py              # Top-level render orchestrator (dispatches to components by theme)
    ├── theme.py               # Theme system (ComponentRegion, ThemeLayout, ThemeStyle)
    ├── layout.py              # Default layout constants
    ├── fonts.py               # Font loader (@lru_cache)
    ├── icons.py               # OWM icon code → Weather Icons glyph
    ├── moon.py                # Moon phase calculator
    ├── primitives.py          # Shared draw utilities (truncation, wrapping, colors)
    ├── themes/                # 6 themes: default, terminal, minimalist, old_fashioned, today, fantasy
    └── components/            # One file per UI region (header, week_view, weather_panel, birthday_bar, today_view, info_panel)

config/
├── config.example.yaml        # Template (copy to config.yaml)
└── quotes.json                # Bundled daily quotes

tests/                         # 25 test files, extensive mocking
fonts/                         # Bundled TTF fonts
deploy/                        # Systemd service + timer
output/                        # Generated PNGs + cache files (git-ignored except latest.png)
credentials/                   # Google service account JSON (git-ignored)
```

## Architecture Patterns

### Per-source independence
Fetchers, caching, circuit breaking, and staleness are all per-source (calendar, weather, birthdays). A weather API failure doesn't block calendar rendering.

### Theme system
Three-layer design: **ComponentRegion** (bounding box) → **ThemeLayout** (canvas + regions + draw order) → **ThemeStyle** (colors, fonts, spacing). Components receive region + style and draw only within bounds. Themes are frozen dataclasses.

### Data flow
`main.py`: parse args → load config → check quiet hours → fetch data (with cache/circuit breaker) → filter events → load theme → render → compare hash → write display → save cache.

### Rendering
Components are pure functions: `draw_*(draw, data, region, style) -> None`. No global state. Same input produces the same PNG.

## Key Conventions

- **Dataclass-first**: pure data models with no I/O in `src/data/models.py`
- **Config mirrors YAML**: dataclass hierarchy in `config.py` matches YAML structure; all fields optional with defaults
- **Max line length**: 100 characters
- **Testing**: heavy use of `unittest.mock.patch`; fixtures for temp dirs and dummy data
- **Thread safety**: cache operations use `threading.Lock()`
- **Graceful degradation**: fetch failure → load cached → use stale data → staleness indicator in header

## CLI Flags

```
--dry-run              Save PNG instead of writing to eInk hardware
--dummy                Use built-in dummy data (no API keys needed)
--config PATH          Custom config file path
--force-full-refresh   Bypass fetch intervals and circuit breaker
--check-config         Validate config and exit
```

## Adding New Features

**New component**: Create `src/render/components/my_component.py` → implement `draw_my_component(draw, data, region, style)` → add `ComponentRegion` to themes → register in `canvas.py` draw dispatch → add to theme `draw_order`.

**New theme**: Create `src/render/themes/my_theme.py` → implement `my_theme() -> Theme` factory → register in `load_theme()` in `theme.py`.

**New fetcher**: Create `src/fetchers/my_fetcher.py` → use `cache.py` and `circuit_breaker.py` → integrate into `main.py` orchestration → extend `DashboardData` if needed.

**New config option**: Add field to relevant dataclass in `config.py` → add to `config.example.yaml` → use in main or components.

## Gotchas

- Incremental sync tokens persist in `calendar_sync_state.json`; delete to force full resync
- Quiet hours (default 23:00–06:00): app exits immediately during this window
- eInk partial refreshes degrade quality; full refresh forced after `max_partials_before_full` partials
- Default canvas: 800×480; scaled via LANCZOS to match display resolution
- Image hash comparison (`last_image_hash.txt`) skips eInk writes when content unchanged
