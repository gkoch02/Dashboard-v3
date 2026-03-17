from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass
class CalendarEvent:
    summary: str
    start: datetime
    end: datetime
    is_all_day: bool = False
    location: Optional[str] = None
    calendar_name: Optional[str] = None
    event_id: Optional[str] = None  # Google Calendar event ID for incremental sync


@dataclass
class DayForecast:
    date: date
    high: float
    low: float
    icon: str
    description: str
    precip_chance: Optional[float] = None  # 0.0–1.0 probability of precipitation


@dataclass
class WeatherAlert:
    event: str  # Short alert name, e.g. "Flood Watch"


@dataclass
class WeatherData:
    current_temp: float
    current_icon: str
    current_description: str
    high: float
    low: float
    humidity: int
    forecast: list[DayForecast] = field(default_factory=list)
    alerts: list[WeatherAlert] = field(default_factory=list)
    feels_like: Optional[float] = None
    wind_speed: Optional[float] = None    # speed in configured units (mph or m/s)
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None


@dataclass
class Birthday:
    name: str
    date: date
    age: Optional[int] = None


@dataclass
class DashboardData:
    events: list[CalendarEvent] = field(default_factory=list)
    weather: Optional[WeatherData] = None
    birthdays: list[Birthday] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=datetime.now)
    is_stale: bool = False  # True when any component was filled from cache
    stale_sources: list[str] = field(default_factory=list)  # e.g. ["events", "weather"]
