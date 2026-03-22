# CLAUDE.md — Dashboard-v3

## Project Overview

Python eInk dashboard for Raspberry Pi. Displays a weekly calendar (Google Calendar), weather (OpenWeatherMap), upcoming birthdays, and a daily quote. Renders to a Waveshare eInk display or PNG preview. No web framework — pure CLI application.

## Quick Commands

```bash
make setup          # Create venv, install deps, copy config template
make test           # Run pytest (636 tests across 31 files)
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
    ├── theme.py               # Theme system (ComponentRegion, ThemeLayout, ThemeStyle); AVAILABLE_THEMES
    ├── random_theme.py        # Daily random theme selection + persistence (output/random_theme_state.json)
    ├── layout.py              # Default layout constants
    ├── fonts.py               # Font loader (@lru_cache)
    ├── icons.py               # OWM icon code → Weather Icons glyph
    ├── moon.py                # Moon phase calculator
    ├── primitives.py          # Shared draw utilities (truncation, wrapping, colors)
    ├── themes/                # 7 themes: default, terminal, minimalist, old_fashioned, today, fantasy, qotd
    └── components/            # One file per UI region (header, week_view, weather_panel, birthday_bar, today_view, info_panel)

config/
├── config.example.yaml        # Template (copy to config.yaml)
└── quotes.json                # Bundled daily quotes

tests/                         # 31 test files, extensive mocking
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

Setting `theme: random` activates daily rotation: `random_theme.py` picks one theme from the eligible pool on the first run after midnight, persists it to `output/random_theme_state.json`, and reuses it for the rest of the day. The concrete theme name is resolved in `main.py` before `load_theme()` is called — `load_theme()` itself never receives `"random"`.

### Data flow
`main.py`: parse args → load config → check quiet hours → fetch data (with cache/circuit breaker) → filter events → resolve theme (random → concrete name) → load theme → render → compare hash → write display → save cache.

### Rendering
Components are pure functions: `draw_*(draw, data, region, style) -> None`. No global state. Same input produces the same PNG.

## Key Conventions

- **Dataclass-first**: pure data models with no I/O in `src/data/models.py`
- **Config mirrors YAML**: dataclass hierarchy in `config.py` matches YAML structure; all fields optional with defaults
- **Max line length**: 100 characters
- **Testing**: heavy use of `unittest.mock.patch`; fixtures for temp dirs and dummy data; every public render function has dedicated smoke tests plus logic unit tests
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

**New theme**: Create `src/render/themes/my_theme.py` → implement `my_theme() -> Theme` factory → register in `load_theme()` in `theme.py` → add name to `AVAILABLE_THEMES`. New themes are automatically included in the `random` rotation pool.

**New fetcher**: Create `src/fetchers/my_fetcher.py` → use `cache.py` and `circuit_breaker.py` → integrate into `main.py` orchestration → extend `DashboardData` if needed.

**New config option**: Add field to relevant dataclass in `config.py` → add to `config.example.yaml` → use in main or components.

## Fonts

### Bundled fonts (`fonts/`)

| File | Accessor(s) in `fonts.py` | Used by |
|---|---|---|
| `PlusJakartaSans-*.ttf` | `regular`, `medium`, `semibold`, `bold` | Default font for all themes |
| `weathericons-regular.ttf` | `weather_icon` | Weather condition icons + moon phase glyphs (all themes) |
| `ShareTechMono-Regular.ttf` | `cyber_mono` | `terminal` — event body text |
| `Maratype.otf` | `maratype` | `terminal` — dashboard title, day column headers, quote body |
| `UESC Display.otf` | `uesc_display` | `terminal` — month band, section labels, quote attribution |
| `Synthetic Genesis.otf` | `synthetic_genesis` | `terminal` — large today date numeral |
| `DMSans.ttf` | `dm_regular/medium/semibold/bold` | `minimalist` |
| `PlayfairDisplay-*.ttf` | `playfair_regular/medium/semibold/bold` | `old_fashioned`, `qotd` |
| `Cinzel.ttf` | `cinzel_regular/semibold/bold/black` | `fantasy`, `old_fashioned` section labels |
| `NuCore.otf` / `NuCore Condensed.otf` | *(unused — available for new themes)* | — |

### `ThemeStyle` font fields

`ThemeStyle` exposes font callables of the form `(size: int) -> FreeTypeFont`. All fields
default to `None` and fall back gracefully so adding a new field never breaks existing themes.

| Field | Fallback | Controls |
|---|---|---|
| `font_regular` | Plus Jakarta Sans Regular | General body text |
| `font_medium` | Plus Jakarta Sans Medium | Mid-weight body text |
| `font_semibold` | Plus Jakarta Sans SemiBold | Emphasis text, event titles |
| `font_bold` | Plus Jakarta Sans Bold | Default for unlisted elements |
| `font_title` | `font_bold` | Dashboard title (header) + day column headers |
| `font_section_label` | `font_bold` (or weight set by `label_font_weight`) | WEATHER / BIRTHDAYS / QUOTE OF THE DAY labels |
| `font_date_number` | `font_bold` | Large today date numeral (bottom-right of week view) |
| `font_month_title` | `font_bold` | Large month name band above the date numeral |
| `font_quote` | `font_regular` | Quote body text in the info panel |
| `font_quote_author` | `font_regular` | Quote attribution line (`— Author`) |

## Gotchas

- Incremental sync tokens persist in `calendar_sync_state.json`; delete to force full resync
- Quiet hours (default 23:00–06:00): app exits immediately during this window
- eInk partial refreshes degrade quality; full refresh forced after `max_partials_before_full` partials
- Default canvas: 800×480; scaled via LANCZOS to match display resolution
- Image hash comparison (`last_image_hash.txt`) skips eInk writes when content unchanged
- Random theme state persists in `output/random_theme_state.json`; delete it to force a new theme pick mid-day
