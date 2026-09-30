"""
Weather tool using Open-Meteo API with offline cache fallback.
"""
import json
import os
import urllib.request
import urllib.parse
from typing import List, Dict, Any
from models import DayWeather

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "cache", "weather.json")

CITY_COORDINATES = {
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Agra": {"lat": 27.1767, "lon": 78.0081},
    "Udaipur": {"lat": 24.5854, "lon": 73.7125},
    "Jodhpur": {"lat": 26.2389, "lon": 73.0243}
}


def _load_cached_weather(city: str, days: int = 3) -> List[DayWeather]:
    """Load weather from local fallback cache."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if city in data and "days" in data[city]:
                    raw_days = data[city]["days"][:days]
                    return [DayWeather(**d) for d in raw_days]
    except Exception as e:
        print(f"[WeatherTool] Cache load error: {e}")

    # Ultimate hardcoded fallback
    return [
        DayWeather(condition="Clear & Sunny", temp=28.0, rain_prob=10, is_rainy=False, summary="Pleasant sunny day"),
        DayWeather(condition="Rain Showers", temp=25.0, rain_prob=80, is_rainy=True, summary="Scattered rain expected"),
        DayWeather(condition="Partly Cloudy", temp=27.0, rain_prob=20, is_rainy=False, summary="Mild pleasant skies")
    ][:days]


def get_weather(city: str = "Jaipur", days: int = 3) -> List[DayWeather]:
    """
    Fetch weather forecast for city from Open-Meteo API.
    Falls back gracefully to cached weather data if network or API fails.
    """
    coords = CITY_COORDINATES.get(city, CITY_COORDINATES["Jaipur"])
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={coords['lat']}&longitude={coords['lon']}&"
        f"daily=temperature_2m_max,precipitation_probability_max,weathercode,windspeed_10m_max&"
        f"timezone=Asia%2FKolkata&forecast_days={max(days, 3)}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TravelSaarthi-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            if response.status == 200:
                raw_json = json.loads(response.read().decode("utf-8"))
                daily = raw_json.get("daily", {})
                temps = daily.get("temperature_2m_max", [])
                rain_probs = daily.get("precipitation_probability_max", [])
                winds = daily.get("windspeed_10m_max", [])
                codes = daily.get("weathercode", [])

                weather_results = []
                for i in range(min(days, len(temps))):
                    prob = int(rain_probs[i]) if i < len(rain_probs) and rain_probs[i] is not None else 15
                    temp = float(temps[i]) if i < len(temps) and temps[i] is not None else 28.0
                    wind = float(winds[i]) if i < len(winds) and winds[i] is not None else 12.0
                    wcode = codes[i] if i < len(codes) else 0

                    is_rainy = prob >= 60 or wcode in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96]
                    if is_rainy:
                        condition = "Rain & Showers"
                        summary = f"Rain probability {prob}%. Outdoor heritage visits may be affected."
                    elif wcode in [1, 2, 3]:
                        condition = "Partly Cloudy"
                        summary = f"Pleasant breeze at {temp}°C, great for photography and walks."
                    else:
                        condition = "Clear & Sunny"
                        summary = f"Bright sunny day at {temp}°C, ideal for sightseeing."

                    weather_results.append(
                        DayWeather(
                            condition=condition,
                            temp=temp,
                            rain_prob=prob,
                            is_rainy=is_rainy,
                            wind_speed=wind,
                            summary=summary
                        )
                    )
                if weather_results:
                    return weather_results
    except Exception as e:
        print(f"[WeatherTool] Open-Meteo API unreachable ({e}). Switching to deterministic cache.")

    return _load_cached_weather(city, days)
