# Home Dashboard

A Python-based eInk dashboard for Raspberry Pi that displays your week's calendar events, current weather, upcoming birthdays, and a daily quote — on any supported Waveshare eInk display (black & white).

![Dashboard preview](output/latest.png)

---

## Features

### Display & Rendering

- **Weekly calendar view** — 7-day grid (Mon–Sun) with timed and all-day events from Google Calendar; event locations shown below each title; per-day busy-ness dots and forecast icons in column headers
- **Multi-day spanning events** — all-day events spanning multiple days render as continuous bars across columns instead of being repeated per-day
- **Adaptive event density** — automatically switches between normal, compact, and dense rendering tiers based on event count per day column; busy days use smaller fonts and tighter spacing to fit more events before showing "+N more"
- **Weather panel** — current conditions, high/low, wind speed with compass direction, UV index, 3-day forecast strip, active weather alerts, and moon phase icon via OpenWeatherMap
- **Extended forecast** — up to 6 days of weather forecast data; small weather icons in each day's column header for a unified week-at-a-glance view
- **Moon phase** — pure-math lunar phase calculation displayed next to the weather label — no API needed
- **Birthdays** — upcoming birthdays from a local JSON file, Google Calendar events, or Google Contacts, shown with a countdown ("Today!", "Tomorrow", "in Nd")
- **Daily quote** — deterministic daily rotation from a configurable quote pool (default pool of 125 quotes spanning sci-fi, science, philosophy, and wit)

### Data & Caching

- **Per-source fetch intervals** — configurable refresh intervals per data source (weather every 30 min, calendar every 2 hours, birthdays once daily); skips API calls when cached data is still within the fetch window
- **Cache TTL with staleness gradation** — cached data progresses through FRESH → AGING → STALE → EXPIRED levels based on configurable per-source TTLs; expired data (>4x TTL) is discarded entirely rather than shown
- **Event filtering** — hide events by calendar name, keyword, or all-day status without removing them from the cache; case-insensitive substring matching keeps configuration simple
- **Incremental calendar sync** — after the first fetch, only changed events are downloaded using Google Calendar sync tokens, reducing API quota usage
- **Parallel data fetching** — calendar, weather, and birthday API calls run concurrently for faster refresh
- **Enhanced weather data** — wind direction (8-point compass), barometric pressure, and UV index extracted from OpenWeatherMap APIs

### Reliability

- **Circuit breaker for flaky APIs** — after N consecutive failures (default 3), stops hitting the failing API for a configurable cooldown period; allows a single "half-open" probe after cooldown and resets on success
- **API quota awareness** — lightweight daily request counter per data source with configurable warning thresholds; auto-resets each day; logs warnings when approaching limits
- **Per-source stale data indicator** — header shows `! Stale` when any source's cached data exceeds its TTL; each source (calendar, weather, birthdays) falls back independently so a single outage doesn't stale unrelated data

### Infrastructure

- **Conditional display refresh** — SHA-256 image diffing skips eInk updates when nothing changed, extending display lifespan and saving power
- **Smart refresh schedule** — configurable quiet hours (default 11 pm–6 am) suppress all updates overnight; the first run each morning triggers a forced full refresh for a clean display start
- **Dry-run mode** — renders to PNG without any hardware, great for development

---

## Hardware

- Raspberry Pi (any model with SPI) — Pi Zero 2 WH recommended
- A supported Waveshare eInk display connected via the 40-pin GPIO HAT

See the [Bill of Materials](#bill-of-materials) below for specific part recommendations and pricing.

---

## Bill of Materials

Everything you need to build the dashboard. A minimal build (Pi Zero 2 W + 7.5" display) runs **~$65–75** all-in.

### Required

| Component | Recommended | Notes | Approx. Price |
|---|---|---|---|
| **Raspberry Pi** | [Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) | Cheapest option; plenty of power for this workload. Buy the **Zero 2 WH** (with headers) to avoid soldering. | $15 |
| | [Pi 4 Model B (2 GB)](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) | If you already own one or want headroom for other tasks | $45 |
| **eInk display** | [Waveshare 7.5" HAT V2](https://www.waveshare.com/7.5inch-e-paper-hat.htm) (800×480, B&W) | The default `epd7in5_V2` model. Plugs directly onto the Pi's 40-pin GPIO header. Includes driver HAT + ribbon cable. | ~$30–35 |
| **MicroSD card** | [SanDisk Ultra 32 GB](https://www.amazon.com/s?k=sandisk+ultra+32gb+microsd) or Samsung Evo Select 32 GB | Class 10 / A1 minimum. 16 GB works but 32 GB is recommended. | ~$8–10 |
| **Power supply** | [Official Pi Zero PSU](https://www.raspberrypi.com/products/micro-usb-power-supply/) (micro-USB, 5 V 2.5 A) for Zero 2 W | Use the [USB-C PSU](https://www.raspberrypi.com/products/type-c-power-supply/) for Pi 4. Third-party supplies are fine if rated ≥ 2.5 A. | ~$8–12 |

### Optional (for mounting)

| Component | Notes | Approx. Price |
|---|---|---|
| **Picture frame** | A standard 7"×5" or 8"×6" frame can be cut/modified to seat the display panel behind the glass | ~$10–20 |
| **3D-printed stand/enclosure** | Many designs available on [Printables](https://www.printables.com) and Thingiverse — search "Waveshare 7.5 eink frame" | Free (print it) |
| **Short micro-USB cable** | For routing power inside a frame or enclosure | ~$5 |

### Display model alternatives

All models in the table below are supported out of the box — just set `display.model` in `config/config.yaml`:

| Model | Resolution | Display size | Notes |
|---|---|---|---|
| `epd7in5` | 640×384 | 7.5" | V1 (older) |
| `epd7in5_V2` | 800×480 | 7.5" | **Default / recommended** |
| `epd7in5_V3` | 800×480 | 7.5" | V3 variant |
| `epd7in5b_V2` | 800×480 | 7.5" | Black/white/red — note: this codebase renders B&W only |
| `epd7in5_HD` | 880×528 | 7.5" | HD variant |
| `epd9in7` | 1200×825 | 9.7" | |
| `epd13in3k` | 1600×1200 | 13.3" | |

> Prices are approximate as of early 2026 and will vary by retailer and region. The [Waveshare website](https://www.waveshare.com) and [approved Raspberry Pi resellers](https://www.raspberrypi.com/products/) are good starting points.

---

## Prerequisites

Before starting, make sure you have the following installed on your development machine (not the Pi):

- **Python 3.9 or newer** — check with `python3 --version`
- **git** — check with `git --version`
- **make** — pre-installed on macOS and most Linux systems; on Windows use WSL

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/gkoch02/Dashboard-v3.git
cd Dashboard-v3
make setup
```

`make setup` creates a Python virtual environment in `venv/` and installs all dependencies.

### 2. Configure

```bash
cp config/config.example.yaml config/config.yaml
```

Open `config/config.yaml` in any text editor and fill in the values below. The Google fields require some setup — see the [Google Calendar Setup](#google-calendar-setup) section for step-by-step instructions.

| Field | What to put here |
|---|---|
| `display.model` | Your Waveshare model name (see Hardware table above) |
| `google.service_account_path` | Path to your downloaded Google service account JSON file (default `credentials/service_account.json` is fine) |
| `google.calendar_id` | Your Google Calendar ID — found in Google Calendar settings (see [Google Calendar Setup](#google-calendar-setup)) |
| `weather.api_key` | Your [OpenWeatherMap](https://openweathermap.org/api) API key (free tier works) |
| `weather.latitude` / `longitude` | Your location — e.g. `40.7128` / `-74.0060` for New York |
| `weather.units` | `imperial` for °F, `metric` for °C |
| `timezone` | Your timezone, e.g. `America/Los_Angeles` or `America/New_York`. Use `local` to follow the system clock. Full list at [Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). |
| `schedule.quiet_hours_start` | Hour (0–23) when the display goes silent overnight — default `23` (11 pm) |
| `schedule.quiet_hours_end` | Hour (0–23) when the display wakes up — default `6` (6 am). The 6:00–6:29 run always does a full refresh. |
| `display.enable_partial_refresh` | Set to `true` to use fast partial refreshes between full ones (see below) |
| `display.max_partials_before_full` | Number of partial refreshes before forcing a full one — default `6` (~3 hours at 30-min polling) |

All fields below are **optional** — sensible defaults apply when omitted:

| Field | What it does | Default |
|---|---|---|
| `cache.weather_ttl_minutes` | How long cached weather data stays usable | `60` |
| `cache.events_ttl_minutes` | How long cached calendar data stays usable | `120` |
| `cache.birthdays_ttl_minutes` | How long cached birthday data stays usable | `1440` |
| `cache.weather_fetch_interval` | Minutes between weather API calls | `30` |
| `cache.events_fetch_interval` | Minutes between calendar API calls | `120` |
| `cache.birthdays_fetch_interval` | Minutes between birthday API calls | `1440` |
| `filters.exclude_calendars` | Calendar names to hide (substring match) | `[]` |
| `filters.exclude_keywords` | Keywords in event titles to hide | `[]` |
| `filters.exclude_all_day` | Hide all-day events | `false` |

### 3. Preview (no hardware needed)

```bash
make dry
```

This renders a preview image to `output/latest.png` using dummy data. Open that file in any image viewer to check the layout before connecting any hardware.

### 4. Run with live data

```bash
venv/bin/python -m src.main --config config/config.yaml
```

This fetches real calendar and weather data and (if connected) pushes to the display.

---

## Google Calendar Setup

You need a **Google service account** — a special credential that lets the dashboard read your calendar without interactive login. This takes about 5 minutes.

### Step 1 — Create a Google Cloud project

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account
2. Click the project dropdown at the top and choose **New Project**
3. Give it any name (e.g. "Home Dashboard") and click **Create**

### Step 2 — Enable the Google Calendar API

1. In the left sidebar, go to **APIs & Services → Library**
2. Search for **Google Calendar API** and click it
3. Click **Enable**

### Step 3 — Create a service account

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → Service account**
3. Give it a name (e.g. "dashboard-reader") and click **Create and Continue**
4. Skip the optional role and user access steps — just click **Done**

### Step 4 — Download the key file

1. Back on the Credentials page, click the service account you just created
2. Go to the **Keys** tab → **Add Key → Create new key → JSON**
3. A `.json` file will download — move it to the `credentials/` folder in this project and name it `service_account.json`

> The `credentials/` folder is git-ignored so this file will never be accidentally committed.

### Step 5 — Share your calendar with the service account

1. Copy the service account's email address from the Credentials page — it looks like `dashboard-reader@your-project.iam.gserviceaccount.com`
2. Open [Google Calendar](https://calendar.google.com) and click the three dots next to the calendar you want to display → **Settings and sharing**
3. Scroll to **Share with specific people**, click **+ Add people**, paste the service account email, and set permission to **See all event details**
4. Click **Send**

### Step 6 — Find your Calendar ID

1. In the same calendar settings page, scroll down to **Integrate calendar**
2. Copy the **Calendar ID** — it looks like `abc123xyz@group.calendar.google.com` (or just your email address for the primary calendar)
3. Paste this value into `google.calendar_id` in `config/config.yaml`

---

## Birthday Configuration

Birthdays can come from three sources — set `birthdays.source` in config to choose:

### `file` (default)

Create `config/birthdays.json`:

```json
[
  {"name": "Alice", "date": "1990-03-20"},
  {"name": "Bob",   "date": "07-04"}
]
```

Use `YYYY-MM-DD` to show age automatically, or `MM-DD` to show the name only.

### `calendar`

Events on your Google Calendar whose title contains the `calendar_keyword` (default: `"Birthday"`) are read automatically. No extra setup needed beyond the Google Calendar steps above.

### `contacts`

> **Note:** This option requires a **Google Workspace** (paid) account with administrator access. It does not work with regular personal Gmail accounts.

Birthdays are pulled directly from Google Contacts via the People API. Setup steps:

1. In [Google Cloud Console](https://console.cloud.google.com), go to **APIs & Services → Library**, search **People API**, and enable it
2. In **Google Workspace Admin** ([admin.google.com](https://admin.google.com)) → **Security → Access and data control → API controls → Manage domain-wide delegation**, click **Add new** and enter:
   - **Client ID**: the service account's numeric client ID (found on its details page in Cloud Console)
   - **OAuth scopes**: `https://www.googleapis.com/auth/contacts.readonly`
3. Add `contacts_email` to `config/config.yaml`:

```yaml
google:
  contacts_email: "you@yourdomain.com"   # the Google Workspace user whose contacts to read

birthdays:
  source: "contacts"
  lookahead_days: 30
```

Ages are calculated automatically when a birth year is stored on the contact.

---

## Deployment on Raspberry Pi

### Step 1 — Enable SPI on the Pi

The eInk display communicates over SPI, which is disabled by default.

```bash
sudo raspi-config
```

Navigate to **Interface Options → SPI → Yes**, then reboot.

### Step 2 — Deploy the project

From your development machine:

```bash
make deploy
```

This rsyncs the project to `~/home-dashboard/` on the Pi (expects `pi@raspberrypi.local` — adjust the `deploy` target in `Makefile` if your Pi has a different hostname or username).

### Step 3 — Set up the virtualenv on the Pi

SSH into the Pi, then:

```bash
sudo apt install swig liblgpio-dev
cd ~/home-dashboard
make setup
venv/bin/pip install -r requirements-pi.txt
```

`make setup` creates the `venv/` virtualenv and installs all core dependencies. The `apt` packages are required by the GPIO/SPI libraries. The final pip step installs the Pi-specific hardware packages (`RPi.GPIO`, `spidev`).

### Step 4 — Install Waveshare display drivers

> **Important:** The Waveshare eInk display drivers are not published on PyPI and cannot be installed with a plain `pip install waveshare_epd`. They must be cloned directly from Waveshare's GitHub repository and installed from the local source tree.

```bash
git clone https://github.com/waveshare/e-Paper ~/e-Paper
cd ~/home-dashboard
venv/bin/pip install ~/e-Paper/RaspberryPi_JetsonNano/python/
```

Verify the install worked:

```bash
venv/bin/python -c "import waveshare_epd; print('waveshare_epd OK')"
```

### Step 5 — Run once to verify

```bash
venv/bin/python -m src.main --config config/config.yaml
```

The display should update. If it doesn't, check that SPI is enabled and the ribbon cable is seated.

### Step 6 — Install the systemd timer

The project ships with `deploy/dashboard.service` and `deploy/dashboard.timer` which run the dashboard every 30 minutes and handle logging automatically. From your development machine:

```bash
make install
```

This copies both units to the Pi, enables the timer, and starts it. Verify with:

```bash
ssh pi@raspberrypi.local "systemctl status dashboard.timer"
```

**How the schedule works:**

| Time window | Behaviour |
|---|---|
| 6:00 am | First run of the day — forced **full** eInk refresh |
| 6:30 am – 10:30 pm | 30-minute partial-refresh polling (full refresh every 6 partials) |
| 11:00 pm – 5:59 am | Quiet hours — process starts, detects quiet window, and exits immediately |

Quiet hours and the wake-up hour are configurable in `config/config.yaml`:

```yaml
schedule:
  quiet_hours_start: 23   # 11 pm
  quiet_hours_end: 6      # 6 am
```

> **Note:** `make install` requires SSH access to `pi@raspberrypi.local`. Adjust the hostname in the `Makefile` `deploy`/`install` targets if your Pi uses a different address.

---

## Development

```bash
make setup        # Create venv and install dependencies
make dry          # Dry-run render with dummy data → output/latest.png
make test         # Run test suite (pytest)
make check        # Validate config file and exit
make deploy       # rsync project to Raspberry Pi
make install      # Copy systemd timer/service to Pi and enable
```

### CLI flags

| Flag | Description |
|---|---|
| `--dry-run` | Save to PNG instead of pushing to display |
| `--dummy` | Use built-in dummy data (no API calls) |
| `--config PATH` | Path to config file (default: `config/config.yaml`) |
| `--force-full-refresh` | Force a full eInk refresh cycle (also bypasses fetch intervals and circuit breakers) |
| `--check-config` | Validate config file and exit |

### Offline development

```bash
venv/bin/python -m src.main --dry-run --dummy
```

No API keys, no hardware, no credentials needed.

---

## Advanced Configuration

### Cache TTL and Fetch Intervals

Control how often each data source is refreshed and how long cached data remains usable after a fetch failure:

```yaml
cache:
  # TTL — data older than 4x these values is discarded (EXPIRED)
  weather_ttl_minutes: 60       # 1 hour
  events_ttl_minutes: 120       # 2 hours
  birthdays_ttl_minutes: 1440   # 24 hours
  # Fetch intervals — skip API calls when cache is younger than this
  weather_fetch_interval: 30    # check weather every 30 min
  events_fetch_interval: 120    # check calendar every 2 hours
  birthdays_fetch_interval: 1440  # check birthdays once per day
```

The staleness system classifies cached data into four levels based on its age relative to the TTL: **FRESH** (within TTL), **AGING** (1–2x TTL), **STALE** (2–4x TTL), and **EXPIRED** (>4x TTL, discarded). The header displays a `! Stale` indicator when any source reaches the STALE level.

### Event Filtering

Hide events from the display without removing them from the cache (important for incremental sync correctness):

```yaml
filters:
  exclude_calendars: ["US Holidays", "Spam Calendar"]
  exclude_keywords: ["OOO", "Focus Time", "Block"]
  exclude_all_day: false
```

All matching is case-insensitive and uses substring matching — `"Holiday"` matches `"US Holidays"`.

### Circuit Breaker

The circuit breaker automatically backs off when an API fails repeatedly, preventing wasted requests and log noise. After 3 consecutive failures, the source is skipped for 30 minutes. A single successful "probe" request after cooldown resets the breaker. These defaults are not yet exposed in config but can be tuned in `src/config.py` (`CacheConfig.max_failures`, `CacheConfig.cooldown_minutes`).

---

## Project Structure

```
Dashboard/
├── config/
│   ├── config.example.yaml   # Copy to config.yaml and fill in secrets
│   └── quotes.json           # Daily quote pool (edit to customise)
├── credentials/              # Google service account JSON (git-ignored)
├── fonts/                    # Bundled TTF fonts (see Typography below)
├── output/                   # Dry-run PNGs and cache (git-ignored)
├── src/
│   ├── main.py               # Entry point
│   ├── config.py             # Config loader
│   ├── data/models.py        # Data model dataclasses
│   ├── display/              # Display drivers (DryRun + Waveshare) + conditional refresh
│   ├── filters.py            # Event filtering (calendar name, keyword, all-day)
│   ├── fetchers/             # API integrations + file-based cache + reliability
│   │   ├── weather.py        # OpenWeatherMap (conditions, extended forecast, alerts, UV)
│   │   ├── calendar.py       # Google Calendar + incremental sync + birthday parsing
│   │   ├── cache.py          # Per-source JSON cache with staleness gradation (TTL-based)
│   │   ├── circuit_breaker.py # Circuit breaker pattern for flaky API resilience
│   │   └── quota_tracker.py  # Daily API call counter with warning thresholds
│   └── render/               # Pure Pillow rendering pipeline
│       ├── canvas.py         # Top-level orchestrator
│       ├── layout.py         # Pixel geometry constants
│       ├── moon.py           # Pure-math moon phase calculator
│       └── components/       # header, week_view, weather_panel, …
├── tests/                    # pytest test suite
├── Makefile
├── requirements.txt          # Core dependencies
└── requirements-pi.txt       # Raspberry Pi hardware dependencies
```

---

## Typography

The display uses four font families, each chosen for a specific role:

| Font | Weight(s) | Used for |
|---|---|---|
| [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans) | Regular, Medium, SemiBold, Bold | UI chrome — header, section labels, timestamps, weather details |
| [Fraunces](https://fonts.google.com/specimen/Fraunces) | Bold (700) | Large weekend day number and month label in the calendar date cell |
| [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed) | Medium, SemiBold | Event titles and all-day event bars in the week view |
| [Lora](https://fonts.google.com/specimen/Lora) | Italic | Quote body text in the info panel |
| Weather Icons | Regular | OWM condition icons |

---

## Dependencies

- [Pillow](https://pillow.readthedocs.io/) — image rendering
- [google-api-python-client](https://googleapis.github.io/google-api-python-client/) — Google Calendar & Google Contacts (People API)
- [requests](https://requests.readthedocs.io/) — OpenWeatherMap API
- [PyYAML](https://pyyaml.org/) — configuration
- [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) + [spidev](https://pypi.org/project/spidev/) — Raspberry Pi hardware (Pi only)
