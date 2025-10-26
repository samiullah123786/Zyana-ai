"""Weather Agent - Get real-time weather data using Open-Meteo API.

Uses Open-Meteo (https://open-meteo.com/) - 100% free, no API key needed.
"""
import logging
import re
import httpx
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class WeatherAgent:
    """Agent for fetching real-time weather and forecast data."""
    
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEOUT = 5.0  # 5 second timeout
    
    # Common Pakistan cities (for quick matching)
    PAKISTAN_CITIES = [
        "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad",
        "multan", "peshawar", "quetta", "sialkot", "gujranwala",
        "hyderabad", "abbottabad", "mardan", "kasur", "rahim yar khan"
    ]
    
    def __init__(self):
        """Initialize weather agent."""
        logger.info("✅ WeatherAgent initialized with Open-Meteo API")
    
    async def get_weather(
        self,
        user_message: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get weather information based on user message.
        
        Args:
            user_message: User's message (e.g., "weather in Karachi")
            user_id: Optional user identifier
            
        Returns:
            Dict with weather data and response message
        """
        try:
            # Extract city name from message
            city = self._extract_city(user_message)
            
            if not city:
                return {
                    "success": False,
                    "message": "Please tell me which city you'd like to check! 🌍\n\nFor example: \"Weather in Karachi\" or \"Temperature in Lahore\"",
                    "city": None,
                    "data": None
                }
            
            # Get coordinates for the city
            lat, lon, city_name = await self._geocode_city(city)
            
            if not lat or not lon:
                return {
                    "success": False,
                    "message": f"Sorry, I couldn't find the location for '{city}'. Could you try another city name?",
                    "city": city,
                    "data": None
                }
            
            # Get weather data
            weather_data = await self._fetch_weather(lat, lon)
            
            if not weather_data:
                return {
                    "success": False,
                    "message": "Couldn't fetch the weather right now, Sami. Please try again later! 🌦",
                    "city": city_name,
                    "data": None
                }
            
            # Format response message
            response_message = self._format_weather_response(city_name, weather_data)
            
            logger.info(f"🌤 Weather in {city_name}: {weather_data.get('temperature')}°C")
            
            return {
                "success": True,
                "message": response_message,
                "city": city_name,
                "data": weather_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error in get_weather: {e}", exc_info=True)
            return {
                "success": False,
                "message": "Oops! Something went wrong while checking the weather. Please try again! 🌡",
                "city": None,
                "data": None
            }
    
    def _extract_city(self, message: str) -> Optional[str]:
        """Extract city name from user message.
        
        Args:
            message: User message
            
        Returns:
            City name or None
        """
        message_lower = message.lower()
        
        # Try to find Pakistan cities first (common case)
        for city in self.PAKISTAN_CITIES:
            if city in message_lower:
                return city.title()
        
        # Pattern matching for "weather in CITY" or "temperature in CITY"
        patterns = [
            r'(?:weather|temperature|forecast|climate)\s+(?:in|for|at)\s+([a-zA-Z\s]+?)(?:\?|$|\s+tomorrow|\s+today)',
            r'(?:in|for)\s+([a-zA-Z\s]+?)\s+(?:weather|temperature|forecast)',
            r'\b([A-Z][a-zA-Z\s]{2,})\s+(?:weather|temperature|forecast)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                # Filter out common words that aren't cities
                if city.lower() not in ['the', 'a', 'an', 'this', 'that', 'how', 'what', 'is', 'today', 'tomorrow']:
                    return city.title()
        
        return None
    
    async def _geocode_city(self, city: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Get latitude and longitude for a city.
        
        Args:
            city: City name
            
        Returns:
            Tuple of (latitude, longitude, formatted_city_name)
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(
                    self.GEOCODING_URL,
                    params={
                        "name": city,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("results"):
                    logger.warning(f"⚠️  No geocoding results for city: {city}")
                    return None, None, None
                
                result = data["results"][0]
                lat = result.get("latitude")
                lon = result.get("longitude")
                city_name = result.get("name")
                country = result.get("country", "")
                
                # Format city name with country
                full_name = f"{city_name}, {country}" if country else city_name
                
                logger.debug(f"✅ Geocoded {city} → {full_name} ({lat}, {lon})")
                
                return lat, lon, full_name
                
        except httpx.TimeoutException:
            logger.error(f"⏰ Geocoding timeout for city: {city}")
            return None, None, None
        except Exception as e:
            logger.error(f"❌ Geocoding error for {city}: {e}")
            return None, None, None
    
    async def _fetch_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather data from Open-Meteo API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Weather data dict or None
        """
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(
                    self.WEATHER_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current_weather": "true",
                        "temperature_unit": "celsius",
                        "windspeed_unit": "kmh",
                        "timezone": "auto"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                current = data.get("current_weather", {})
                
                if not current:
                    logger.warning(f"⚠️  No current weather data for ({lat}, {lon})")
                    return None
                
                # Map weather codes to descriptions
                weather_code = current.get("weathercode", 0)
                description = self._get_weather_description(weather_code)
                
                weather_data = {
                    "temperature": current.get("temperature"),
                    "windspeed": current.get("windspeed"),
                    "wind_direction": current.get("winddirection"),
                    "weather_code": weather_code,
                    "description": description,
                    "time": current.get("time")
                }
                
                logger.debug(f"✅ Fetched weather data: {weather_data}")
                
                return weather_data
                
        except httpx.TimeoutException:
            logger.error(f"⏰ Weather API timeout for ({lat}, {lon})")
            return None
        except Exception as e:
            logger.error(f"❌ Weather API error for ({lat}, {lon}): {e}")
            return None
    
    def _get_weather_description(self, code: int) -> str:
        """Convert weather code to human-readable description.
        
        Args:
            code: WMO weather code
            
        Returns:
            Weather description
        """
        # WMO Weather interpretation codes
        weather_codes = {
            0: "Clear sky ☀️",
            1: "Mainly clear 🌤",
            2: "Partly cloudy ⛅",
            3: "Overcast ☁️",
            45: "Foggy 🌫",
            48: "Rime fog 🌫",
            51: "Light drizzle 🌦",
            53: "Moderate drizzle 🌦",
            55: "Dense drizzle 🌧",
            61: "Slight rain 🌧",
            63: "Moderate rain 🌧",
            65: "Heavy rain 🌧",
            71: "Slight snow 🌨",
            73: "Moderate snow 🌨",
            75: "Heavy snow 🌨",
            77: "Snow grains ❄️",
            80: "Slight rain showers 🌦",
            81: "Moderate rain showers 🌧",
            82: "Violent rain showers ⛈",
            85: "Slight snow showers 🌨",
            86: "Heavy snow showers 🌨",
            95: "Thunderstorm ⛈",
            96: "Thunderstorm with hail ⛈",
            99: "Thunderstorm with heavy hail ⛈"
        }
        
        return weather_codes.get(code, "Unknown ❓")
    
    def _format_weather_response(self, city: str, weather_data: Dict[str, Any]) -> str:
        """Format weather data into a user-friendly message.
        
        Args:
            city: City name
            weather_data: Weather data dict
            
        Returns:
            Formatted message string
        """
        temp = weather_data.get("temperature", "N/A")
        windspeed = weather_data.get("windspeed", "N/A")
        description = weather_data.get("description", "Unknown")
        
        message = f"""🌤 **Weather in {city}**

🌡 Temperature: **{temp}°C**
💨 Wind Speed: **{windspeed} km/h**
☁️ Conditions: **{description}**

Stay comfortable, Sami! 😊"""
        
        return message


# Global instance
weather_agent = WeatherAgent()

