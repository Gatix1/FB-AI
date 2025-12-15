import requests
from datetime import datetime
import random

def _clean_text(text: str) -> str:
    return (
        text.replace("?", "")
            .replace(".", "")
            .replace(",", "")
            .strip()
    )

def get_current_time():
    now = datetime.now()
    return now.strftime("The current time is %H:%M.")

def get_current_date():
    now = datetime.now()
    return now.strftime("Today's date is %B %d, %Y.")

def get_weather(city="London"):
    city_clean = _clean_text(city)

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city_clean}&count=1&language=en&format=json"
    )

    try:
        geo_response = requests.get(geo_url, timeout=5)
    except Exception as e:
        return f"Sorry, I could not reach the geocoding service. ({e.__class__.__name__})"

    if geo_response.status_code != 200:
        return f"Sorry, I could not retrieve location data for {city_clean} (status {geo_response.status_code})."

    try:
        geo_data = geo_response.json()
    except ValueError:
        return f"Sorry, I could not parse location data for {city_clean}."

    if "results" not in geo_data or not geo_data["results"]:
        return f"Sorry, I could not find any location for '{city_clean}'."


    first_result = geo_data["results"][0]
    lat = first_result["latitude"]
    lon = first_result["longitude"]
    resolved_name = first_result.get("name", city_clean)


    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
    )

    try:
        weather_response = requests.get(weather_url, timeout=5)
    except Exception as e:
        return f"Sorry, I could not reach the weather service. ({e.__class__.__name__})"

    if weather_response.status_code != 200:
        return (
            f"Sorry, I could not retrieve weather data for {resolved_name} "
            f"(status {weather_response.status_code})."
        )

    try:
        weather_data = weather_response.json()
        current = weather_data["current_weather"]
        temp_c = current["temperature"]
        wind = current["windspeed"]
        return (
            f"The current temperature in {resolved_name} is {temp_c}°C "
            f"with wind speed {wind} km/h."
        )
    except Exception:
        return f"Sorry, weather information is incomplete for {resolved_name}."

def get_bitcoin_price():
    try:
        url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
        response = requests.get(url, timeout=5)
        data = response.json()
        price = data["data"]["amount"]
        return f"The current Bitcoin price is {price} USD."
    except Exception as e:
        return f"Sorry, I could not retrieve Bitcoin price. ({e.__class__.__name__})"

if __name__ == "__main__":
    print(get_current_time())
    print(get_current_date())
    print(get_bitcoin_price())
    print(get_weather("Paris"))
    print(get_weather("Istanbul"))
    print(get_weather("Chisinau"))
