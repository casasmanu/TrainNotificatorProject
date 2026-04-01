import requests
import logging
import os
from datetime import datetime, timedelta
import time
from Drivers.drvTelegram import bot_send_msg, bot_send_msg_to_chat

logger = logging.getLogger(__name__)

# Munich coordinates
MUNICH_LAT = 48.1351
MUNICH_LON = 11.5820

WEATHER_DESCRIPTIONS = {
    "clear sky": "☀️ Cielo despejado",
    "few clouds": "🌤️ Pocas nubes",
    "scattered clouds": "⛅ Nubes dispersas",
    "broken clouds": "☁️ Nublado",
    "shower rain": "🌧️ Lluvia",
    "rain": "🌧️ Lluvia",
    "thunderstorm": "⛈️ Tormenta",
    "snow": "❄️ Nieve",
    "mist": "🌫️ Niebla",
    "fog": "🌫️ Niebla",
}

CLOTHING_RECOMMENDATIONS = {
    "very_cold": {
        "temp": "≤ 0°C",
        "rain": "Abrigo grueso, guantes, gorro, bufanda. Impermeable si llueve.",
        "no_rain": "Abrigo grueso, guantes, gorro, bufanda.",
    },
    "cold": {
        "temp": "1-8°C",
        "rain": "Abrigo, impermeable, bufanda, gorro.",
        "no_rain": "Abrigo, bufanda, gorro.",
    },
    "cool": {
        "temp": "9-15°C",
        "rain": "Chaqueta, impermeable o paraguas.",
        "no_rain": "Chaqueta ligera.",
    },
    "mild": {
        "temp": "16-20°C",
        "rain": "Chaqueta ligera o sudadera, paraguas.",
        "no_rain": "Sudadera o chaqueta ligera.",
    },
    "warm": {
        "temp": "21-25°C",
        "rain": "Ropa ligera, paraguas.",
        "no_rain": "Ropa ligera.",
    },
    "hot": {
        "temp": "> 25°C",
        "rain": "Ropa ligera, paraguas, gafas de sol.",
        "no_rain": "Ropa ligera, gafas de sol, protector solar.",
    },
}


def _get_temperature_category(temp):
    """Categorize temperature for clothing recommendations"""
    if temp <= 0:
        return "very_cold"
    elif temp <= 8:
        return "cold"
    elif temp <= 15:
        return "cool"
    elif temp <= 20:
        return "mild"
    elif temp <= 25:
        return "warm"
    else:
        return "hot"


def _get_weather_description(weather_main):
    """Get emoji and description for weather condition"""
    weather_lower = weather_main.lower()
    for key, value in WEATHER_DESCRIPTIONS.items():
        if key in weather_lower:
            return value
    return f"Weather: {weather_main}"


def _get_clothing_advice(temp, is_raining):
    """Get clothing recommendations based on temperature and rain"""
    category = _get_temperature_category(temp)
    rain_key = "rain" if is_raining else "no_rain"
    advice = CLOTHING_RECOMMENDATIONS[category][rain_key]
    return advice


def _request_with_retry(url, params, timeout=10, retries=6, backoff_seconds=5):
    last_error = None
    retryable_statuses = {429, 500, 502, 503, 504}

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code in retryable_statuses and attempt < retries:
                logger.warning(f"Weather API temporary error {response.status_code}, retry {attempt}/{retries}")
                time.sleep(backoff_seconds * attempt)
                continue
            return response
        except requests.exceptions.SSLError as ssl_error:
            last_error = ssl_error
            if attempt < retries:
                wait = backoff_seconds * attempt
                logger.warning(f"Weather API SSL error (EOF), retry {attempt}/{retries} in {wait}s: {ssl_error}")
                time.sleep(wait)
                continue
            raise
        except (requests.Timeout, requests.ConnectionError) as request_error:
            last_error = request_error
            if attempt < retries:
                logger.warning(f"Weather API timeout/connection issue, retry {attempt}/{retries}")
                time.sleep(backoff_seconds * attempt)
                continue
            raise

    if last_error:
        raise last_error
    raise Exception("Weather API request failed after retries")


def _get_local_date(forecast_entry, timezone_offset_seconds):
    utc_time = datetime.utcfromtimestamp(forecast_entry.get("dt", 0))
    local_time = utc_time + timedelta(seconds=timezone_offset_seconds)
    return local_time.date()


def _extract_daily_summary(data, day_offset=0):
    city_timezone_offset = data.get("city", {}).get("timezone", 0)
    local_now = datetime.utcnow() + timedelta(seconds=city_timezone_offset)
    target_date = (local_now + timedelta(days=day_offset)).date()

    day_entries = [
        entry
        for entry in data.get("list", [])
        if _get_local_date(entry, city_timezone_offset) == target_date
    ]

    if not day_entries:
        raise Exception("No hay datos de pronóstico para la fecha solicitada")

    temp_min = min(entry.get("main", {}).get("temp_min", 999) for entry in day_entries)
    temp_max = max(entry.get("main", {}).get("temp_max", -999) for entry in day_entries)
    avg_temp = (temp_min + temp_max) / 2

    max_rain_prob = max(entry.get("pop", 0) * 100 for entry in day_entries)
    total_rain = sum(entry.get("rain", {}).get("3h", 0) for entry in day_entries)

    weather_counts = {}
    weather_desc_counts = {}
    for entry in day_entries:
        weather = (entry.get("weather") or [{}])[0]
        main = weather.get("main", "")
        desc = weather.get("description", "")
        weather_counts[main] = weather_counts.get(main, 0) + 1
        weather_desc_counts[desc] = weather_desc_counts.get(desc, 0) + 1

    dominant_weather_main = max(weather_counts, key=weather_counts.get) if weather_counts else ""
    dominant_weather_desc = max(weather_desc_counts, key=weather_desc_counts.get) if weather_desc_counts else ""

    return {
        "temp_min": temp_min,
        "temp_max": temp_max,
        "temp_avg": avg_temp,
        "weather_main": dominant_weather_main,
        "weather_desc": dominant_weather_desc,
        "rain_prob_max": max_rain_prob,
        "rain_total": total_rain,
    }


def _send_message(message, chat_id=None):
    if chat_id is None:
        bot_send_msg(message)
    else:
        bot_send_msg_to_chat(chat_id, message)


def getWeatherToday(chat_id=None):
    """Get today's weather forecast and send recommendation"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        logger.error("OPENWEATHER_API_KEY not found in .env")
        _send_message("❌ Error: API key de OpenWeatherMap no configurada", chat_id=chat_id)
        return
    
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": MUNICH_LAT,
            "lon": MUNICH_LON,
            "appid": api_key,
            "units": "metric",
            "lang": "es"
        }
        
        logger.info("Fetching today's weather forecast")
        response = _request_with_retry(url, params=params, timeout=10, retries=6, backoff_seconds=1.5)
        
        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}: {response.text}")
        
        data = response.json()
        
        summary = _extract_daily_summary(data, day_offset=0)

        temp_min = summary["temp_min"]
        temp_max = summary["temp_max"]
        temp_avg = summary["temp_avg"]
        weather_main = summary["weather_main"]
        weather_desc = summary["weather_desc"]
        rain_prob = summary["rain_prob_max"]
        rain_volume = summary["rain_total"]

        is_raining = rain_prob > 30 or rain_volume > 0
        weather_emoji = _get_weather_description(weather_main)
        clothing_advice = _get_clothing_advice(temp_avg, is_raining)
        
        message = f"""🌍 Clima de Hoy - Múnich

{weather_emoji}
Descripción: {weather_desc}

🌡️ Rango del día: {temp_min:.1f}°C - {temp_max:.1f}°C
💧 Probabilidad máxima de lluvia: {rain_prob:.0f}%
🌧️ Lluvia acumulada estimada: {rain_volume:.1f} mm

👕 Recomendación de ropa:
{clothing_advice}
"""
        
        logger.info("Today's weather retrieved successfully")
        _send_message(message, chat_id=chat_id)
        
    except Exception as e:
        logger.error(f"Error fetching today's weather: {e}")
        _send_message(f"❌ Error obteniendo clima de hoy: {str(e)}", chat_id=chat_id)

def getWeatherTomorrow(chat_id=None):
    """Get tomorrow's weather forecast and send recommendation"""
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        logger.error("OPENWEATHER_API_KEY not found in .env")
        _send_message("❌ Error: API key de OpenWeatherMap no configurada", chat_id=chat_id)
        return
    
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": MUNICH_LAT,
            "lon": MUNICH_LON,
            "appid": api_key,
            "units": "metric",
            "lang": "es"
        }
        
        logger.info("Fetching tomorrow's weather forecast")
        response = _request_with_retry(url, params=params, timeout=10, retries=6, backoff_seconds=1.5)
        
        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}: {response.text}")
        
        data = response.json()
        
        summary = _extract_daily_summary(data, day_offset=1)

        temp_min = summary["temp_min"]
        temp_max = summary["temp_max"]
        temp_avg = summary["temp_avg"]
        weather_main = summary["weather_main"]
        weather_desc = summary["weather_desc"]
        rain_prob = summary["rain_prob_max"]
        rain_volume = summary["rain_total"]

        is_raining = rain_prob > 30 or rain_volume > 0
        weather_emoji = _get_weather_description(weather_main)
        clothing_advice = _get_clothing_advice(temp_avg, is_raining)
        
        message = f"""🌍 Clima de Mañana - Múnich

{weather_emoji}
Descripción: {weather_desc}

🌡️ Rango del día: {temp_min:.1f}°C - {temp_max:.1f}°C
💧 Probabilidad máxima de lluvia: {rain_prob:.0f}%
🌧️ Lluvia acumulada estimada: {rain_volume:.1f} mm

👕 Recomendación de ropa:
{clothing_advice}
"""
        
        logger.info("Tomorrow's weather retrieved successfully")
        _send_message(message, chat_id=chat_id)
        
    except Exception as e:
        logger.error(f"Error fetching tomorrow's weather: {e}")
        _send_message(f"❌ Error obteniendo clima de mañana: {str(e)}", chat_id=chat_id)


# ---------------------------------------------------------------------------
# Weekly summary & rain/snow alert helpers
# ---------------------------------------------------------------------------

DAYS_ES = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

PRECIPITATION_MAINS = {"Rain", "Drizzle", "Thunderstorm", "Snow"}


def _is_precipitation(weather_main, rain_prob, volume):
    return weather_main in PRECIPITATION_MAINS or rain_prob > 40 or volume > 0


def _get_precipitation_label(weather_main, has_snow):
    if has_snow or weather_main == "Snow":
        return "❄️ nieve"
    if weather_main == "Thunderstorm":
        return "⛈️ tormenta"
    return "🌧️ lluvia"


def _check_day_periods(day_entries, timezone_offset_seconds):
    """Return precipitation info per period (mañana/tarde) for a single day."""
    morning = []   # 06:00 – 12:00
    afternoon = [] # 12:00 – 20:00

    for entry in day_entries:
        utc_time = datetime.utcfromtimestamp(entry.get("dt", 0))
        local_time = utc_time + timedelta(seconds=timezone_offset_seconds)
        hour = local_time.hour
        if 6 <= hour < 12:
            morning.append(entry)
        elif 12 <= hour < 20:
            afternoon.append(entry)

    result = {}
    for period_name, entries in [("mañana", morning), ("tarde", afternoon)]:
        if not entries:
            continue
        max_rain_prob = max(e.get("pop", 0) * 100 for e in entries)
        total_rain = sum(e.get("rain", {}).get("3h", 0) for e in entries)
        total_snow = sum(e.get("snow", {}).get("3h", 0) for e in entries)
        weather_mains = [(e.get("weather") or [{}])[0].get("main", "") for e in entries]
        dominant = max(set(weather_mains), key=weather_mains.count) if weather_mains else ""

        if _is_precipitation(dominant, max_rain_prob, total_rain + total_snow):
            result[period_name] = {
                "label": _get_precipitation_label(dominant, total_snow > 0),
                "prob": max_rain_prob,
            }
    return result


# ---------------------------------------------------------------------------
# Weekly summary (intended for Sunday nights)
# ---------------------------------------------------------------------------

def getWeeklySummary(chat_id=None):
    """Send a weather summary for the coming week (best called on Sunday nights)."""
    api_key = os.getenv('OPENWEATHER_API_KEY')

    if not api_key:
        logger.error("OPENWEATHER_API_KEY not found in .env")
        _send_message("❌ Error: API key de OpenWeatherMap no configurada", chat_id=chat_id)
        return

    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": MUNICH_LAT,
            "lon": MUNICH_LON,
            "appid": api_key,
            "units": "metric",
            "lang": "es",
        }

        logger.info("Fetching weekly weather forecast")
        response = _request_with_retry(url, params=params, timeout=10, retries=6, backoff_seconds=5)

        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}: {response.text}")

        data = response.json()
        city_timezone_offset = data.get("city", {}).get("timezone", 0)
        local_now = datetime.utcnow() + timedelta(seconds=city_timezone_offset)

        lines = ["📅 Resumen meteorológico de la semana — Múnich\n"]

        for day_offset in range(1, 6):  # up to 5 days (free plan limit)
            try:
                summary = _extract_daily_summary(data, day_offset=day_offset)
                target_date = (local_now + timedelta(days=day_offset)).date()
                day_name = DAYS_ES[target_date.weekday()]
                date_str = target_date.strftime("%d/%m")

                weather_emoji = _get_weather_description(summary["weather_main"])

                has_snow = "snow" in summary["weather_main"].lower()
                has_rain = summary["rain_prob_max"] > 40 or summary["rain_total"] > 0
                warn = "❄️ " if has_snow else ("💧 " if has_rain else "")

                lines.append(
                    f"{warn}{day_name} {date_str}: {summary['temp_min']:.0f}°C – {summary['temp_max']:.0f}°C  {weather_emoji}\n"
                    f"   Lluvia: {summary['rain_prob_max']:.0f}%  {summary['rain_total']:.1f}mm\n"
                )
            except Exception:
                pass

        logger.info("Weekly weather summary sent successfully")
        _send_message("".join(lines), chat_id=chat_id)

    except Exception as e:
        logger.error(f"Error fetching weekly weather: {e}")
        _send_message(f"❌ Error obteniendo resumen semanal: {str(e)}", chat_id=chat_id)


# ---------------------------------------------------------------------------
# Daily rain/snow alert for the next 4 days
# ---------------------------------------------------------------------------

def checkRainSnowAlert(chat_id=None):
    """Check the next 4 days and send an alert ONLY if rain or snow is expected."""
    api_key = os.getenv('OPENWEATHER_API_KEY')

    if not api_key:
        logger.error("OPENWEATHER_API_KEY not found in .env")
        return

    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": MUNICH_LAT,
            "lon": MUNICH_LON,
            "appid": api_key,
            "units": "metric",
            "lang": "es",
        }

        logger.info("Checking rain/snow alert for next 4 days")
        response = _request_with_retry(url, params=params, timeout=10, retries=6, backoff_seconds=5)

        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}: {response.text}")

        data = response.json()
        city_timezone_offset = data.get("city", {}).get("timezone", 0)
        local_now = datetime.utcnow() + timedelta(seconds=city_timezone_offset)

        alert_lines = []

        for day_offset in range(1, 5):  # next 4 days
            target_date = (local_now + timedelta(days=day_offset)).date()
            day_name = DAYS_ES[target_date.weekday()]
            date_str = target_date.strftime("%d/%m")

            day_entries = [
                entry
                for entry in data.get("list", [])
                if _get_local_date(entry, city_timezone_offset) == target_date
            ]

            if not day_entries:
                continue

            periods = _check_day_periods(day_entries, city_timezone_offset)
            if not periods:
                continue

            period_strs = [
                f"por la {name} ({info['label']}, {info['prob']:.0f}%)"
                for name, info in periods.items()
            ]
            alert_lines.append(f"• {day_name} {date_str}: {' y '.join(period_strs)}")

        if alert_lines:
            message = "⚠️ Alerta lluvia/nieve — próximos días:\n\n" + "\n".join(alert_lines)
            logger.info(f"Rain/snow alert sent for {len(alert_lines)} day(s)")
            _send_message(message, chat_id=chat_id)
        else:
            logger.info("No rain/snow expected in the next 4 days, no alert sent")

    except Exception as e:
        logger.error(f"Error checking rain/snow alert: {e}")
        _send_message(f"❌ Error verificando alerta de lluvia/nieve: {str(e)}", chat_id=chat_id)
