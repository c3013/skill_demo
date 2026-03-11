"""Weather skill – mock weather lookup (no external API required)."""

import random

from langchain_core.tools import tool

# Simulated weather data so the demo runs without any external API key.
_MOCK_WEATHER: dict[str, dict] = {
    "beijing": {"condition": "Sunny", "temp_c": 22, "humidity": 40},
    "shanghai": {"condition": "Cloudy", "temp_c": 18, "humidity": 65},
    "new york": {"condition": "Rainy", "temp_c": 10, "humidity": 80},
    "london": {"condition": "Foggy", "temp_c": 8, "humidity": 90},
    "tokyo": {"condition": "Clear", "temp_c": 15, "humidity": 55},
}


@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city (mock data). Args: city – name of the city."""
    key = city.strip().lower()
    if key in _MOCK_WEATHER:
        data = _MOCK_WEATHER[key]
    else:
        # Return randomised data for unknown cities to keep demo self-contained.
        data = {
            "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Snowy"]),
            "temp_c": random.randint(-5, 35),
            "humidity": random.randint(20, 95),
        }
    return (
        f"Weather in {city.title()}: {data['condition']}, "
        f"{data['temp_c']}°C, humidity {data['humidity']}%."
    )


@tool
def list_supported_cities() -> list:
    """Return the list of cities for which real (mock) weather data is available."""
    return [city.title() for city in _MOCK_WEATHER]
