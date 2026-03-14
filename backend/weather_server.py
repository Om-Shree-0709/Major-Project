"""
Weather MCP Server
Uses Open-Meteo API (free, no API key required)
and Nominatim for geocoding (free, no API key required)
"""
import logging
import requests
from typing import Dict, Any, List

try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

logger = logging.getLogger("weather_mcp_server")
logger.setLevel(logging.INFO)

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
}

class WeatherMCPServer(IMCPExternalServer):
    """Weather MCP Server using Open-Meteo (no API key needed)."""

    def __init__(self):
        super().__init__(name="weather")
        logger.info("Weather MCP Server initialized")

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="weather.get_current",
                description="Get current weather for a city",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name e.g. 'London' or 'New York'"}
                    },
                    "required": ["city"]
                }
            ),
            MCPTool(
                name="weather.get_forecast",
                description="Get 7-day weather forecast for a city",
                parameters={
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"]
                }
            )
        ]

    def _geocode(self, city: str) -> Dict[str, Any]:
        """Convert city name to lat/lon using Nominatim."""
        try:
            resp = requests.get(
                GEOCODE_URL,
                params={"q": city, "format": "json", "limit": 1},
                headers={"User-Agent": "MCPWeatherServer/1.0"},
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return {"error": f"City '{city}' not found"}
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "name": data[0].get("display_name", city)}
        except Exception as e:
            return {"error": str(e)}

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        city = args.get("city", "").strip()
        if not city:
            return {"error": "City name is required", "code": 400}

        geo = self._geocode(city)
        if "error" in geo:
            return {"error": geo["error"], "code": 404}

        lat, lon = geo["lat"], geo["lon"]

        try:
            if tool_name == "weather.get_current":
                resp = requests.get(
                    WEATHER_URL,
                    params={
                        "latitude": lat, "longitude": lon,
                        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode",
                        "timezone": "auto"
                    },
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                current = data.get("current", {})
                return {
                    "city": city,
                    "location": geo["name"],
                    "temperature_c": current.get("temperature_2m"),
                    "humidity_percent": current.get("relative_humidity_2m"),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                    "condition": WMO_CODES.get(current.get("weathercode", 0), "Unknown"),
                    "code": 200
                }

            elif tool_name == "weather.get_forecast":
                resp = requests.get(
                    WEATHER_URL,
                    params={
                        "latitude": lat, "longitude": lon,
                        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum",
                        "timezone": "auto",
                        "forecast_days": 7
                    },
                    timeout=10
                )
                resp.raise_for_status()
                data = resp.json()
                daily = data.get("daily", {})
                dates = daily.get("time", [])
                forecast = []
                for i, date in enumerate(dates):
                    forecast.append({
                        "date": date,
                        "max_temp_c": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                        "min_temp_c": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                        "condition": WMO_CODES.get(daily.get("weathercode", [])[i] if i < len(daily.get("weathercode", [])) else 0, "Unknown"),
                        "precipitation_mm": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else None
                    })
                return {"city": city, "location": geo["name"], "forecast": forecast, "code": 200}

            return {"error": f"Tool {tool_name} not found", "code": 404}

        except requests.Timeout:
            return {"error": "Weather request timed out", "code": 408}
        except Exception as e:
            logger.exception(f"Weather tool error: {e}")
            return {"error": str(e), "code": 500}
