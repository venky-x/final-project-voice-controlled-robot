from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import requests

# Conversion of  weather codes to human-readable form
WEATHER_CODE_MAP = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "cloudy",  
    45: "foggy",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    95: "thunderstorm",
    96: "thunderstorm with light hail",
    99: "thunderstorm with heavy hail"
}

class ActionGetWeather(Action):
    def name(self) -> str:
        return "action_get_weather"

    def run(self, dispatcher, tracker, domain):
        try:
            # Fetch weather from Open-Meteo for Singapore (lat: 1.3521, lon: 103.8198)
            url = "https://api.open-meteo.com/v1/forecast?latitude=1.3521&longitude=103.8198&current_weather=true"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Extract temperature and weather code
            weather_data = data["current_weather"]
            temp = weather_data["temperature"]
            weather_code = weather_data["weathercode"]
            print(f"Debug: Received weather code = {weather_code}")  # Add this for debugging

            # Map weather code to a human-readable form
            condition = WEATHER_CODE_MAP.get(weather_code, "unknown")

            # Send response
            dispatcher.utter_message(
                response="utter_weather",
                condition=condition,
                temp=temp
            )
        except Exception as e:
            print(f"Weather fetch error: {e}")
            dispatcher.utter_message(response="utter_weather_error")

        return []
