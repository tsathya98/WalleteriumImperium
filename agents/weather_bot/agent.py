import datetime
from zoneinfo import ZoneInfo

from geopy.geocoders import Nominatim
from google.adk.agents import Agent
from timezonefinder import TimezoneFinder

# Initialize geocoder and timezone finder
geolocator = Nominatim(user_agent="weather_time_agent")
tf = TimezoneFinder()


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city using OpenWeatherMap API.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    try:
        # Note: In production, you should use a real API key from OpenWeatherMap
        # For demo purposes, we'll return simulated data based on common cities
        # To use real data, sign up at https://openweathermap.org/api

        # Simulate weather data for demonstration
        weather_data = {
            "new york": "sunny, 25°C (77°F)",
            "london": "cloudy, 15°C (59°F)",
            "tokyo": "partly cloudy, 22°C (72°F)",
            "paris": "rainy, 18°C (64°F)",
            "sydney": "sunny, 28°C (82°F)",
            "mumbai": "humid, 32°C (90°F)",
            "moscow": "snowy, -5°C (23°F)",
            "cairo": "sunny, 30°C (86°F)",
            "beijing": "foggy, 20°C (68°F)",
            "los angeles": "sunny, 24°C (75°F)",
        }

        city_lower = city.lower()
        if city_lower in weather_data:
            return {
                "status": "success",
                "report": f"The weather in {city} is {weather_data[city_lower]}.",
            }
        else:
            # For unknown cities, provide a generic response
            return {
                "status": "success",
                "report": f"Weather information for '{city}' is not available in the demo. "
                f"To get real-time weather data, integrate with OpenWeatherMap API using your API key.",
            }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving weather for '{city}': {str(e)}",
        }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city using global timezone data.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """
    try:
        # Get coordinates for the city
        location = geolocator.geocode(city)
        if not location:
            return {
                "status": "error",
                "error_message": f"Could not find location data for '{city}'. Please check the city name.",
            }

        # Get timezone for the coordinates
        timezone_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
        if not timezone_str:
            return {
                "status": "error",
                "error_message": f"Could not determine timezone for '{city}'.",
            }

        # Get current time in that timezone
        tz = ZoneInfo(timezone_str)
        now = datetime.datetime.now(tz)

        report = (
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")} '
            f'(Timezone: {timezone_str})'
        )

        return {"status": "success", "report": report}

    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error getting time for '{city}': {str(e)}",
        }


root_agent = Agent(
    name="global_weather_time_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to answer questions about the time and weather in cities worldwide."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in any city around the world. "
        "For time queries, I can provide accurate current time for any city using geographic coordinates and timezone data. "
        "For weather queries, I currently provide simulated data for demonstration purposes - to get real weather data, "
        "you would need to integrate with a weather API service like OpenWeatherMap."
    ),
    tools=[get_weather, get_current_time],
)
