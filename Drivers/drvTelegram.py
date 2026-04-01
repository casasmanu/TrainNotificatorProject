import telebot
import logging
import os
logger = logging.getLogger(__name__)

_weather_command_offset = None
_weather_command_initialized = False

# --------------------- Import Variables ----------------------- #

import __main__


def _get_runtime_telegram_config():
    token = getattr(__main__, 'botToken', None) or os.getenv('BOT_TOKEN')
    destinatary = getattr(__main__, 'destinatary', None) or os.getenv('BOT_DESTINATARY')
    return token, destinatary

#define usefull functions
def bot_send_msg(msg):
    token, destinatary = _get_runtime_telegram_config()
    if token is None or destinatary is None:
        logger.error("Bot token or destinatary not available, skipping message send")
        return
    try:
        bot = telebot.TeleBot(token)
        bot.send_message(destinatary, msg)
        logger.info("message sent succesfully")
    except Exception as e:
        logger.error(f"Problem while trying to send a msg: {e}")
    return


def bot_send_msg_to_chat(chat_id, msg):
    token, _ = _get_runtime_telegram_config()
    if token is None:
        logger.error("Bot token not available, skipping chat message send")
        return
    try:
        bot = telebot.TeleBot(token)
        bot.send_message(chat_id, msg)
        logger.info(f"message sent succesfully to chat {chat_id}")
    except Exception as e:
        logger.error(f"Problem while trying to send a chat msg: {e}")
    return


def _parse_weather_command(text):
    if not text:
        return None

    normalized_text = text.strip().lower()
    parts = normalized_text.split()

    if not parts or parts[0] != '/clima':
        return None

    if len(parts) < 2:
        return 'invalid'

    day = parts[1]
    if day == 'hoy':
        return 'today'
    if day in ('manana', 'mañana'):
        return 'tomorrow'

    return 'invalid'


def poll_weather_commands():
    global _weather_command_offset
    global _weather_command_initialized

    token, _ = _get_runtime_telegram_config()
    if token is None:
        logger.error("Bot token not available, cannot poll weather commands")
        return

    bot = telebot.TeleBot(token)

    try:
        updates = bot.get_updates(offset=_weather_command_offset, timeout=0)
    except Exception as e:
        logger.error(f"Error polling weather commands: {e}")
        return

    if not updates:
        return

    if not _weather_command_initialized:
        _weather_command_offset = updates[-1].update_id + 1
        _weather_command_initialized = True
        logger.info("Weather command polling initialized; old updates skipped")
        return

    for update in updates:
        _weather_command_offset = update.update_id + 1

        message = getattr(update, 'message', None)
        if message is None:
            continue

        parsed_command = _parse_weather_command(getattr(message, 'text', ''))
        if parsed_command is None:
            continue

        if parsed_command == 'invalid':
            bot.reply_to(message, "Uso: /clima hoy o /clima mañana")
            continue

        bot.reply_to(message, "Consultando clima, un segundo...")

        if parsed_command == 'today':
            from Drivers.drvWeather import getWeatherToday
            getWeatherToday(chat_id=message.chat.id)
        elif parsed_command == 'tomorrow':
            from Drivers.drvWeather import getWeatherTomorrow
            getWeatherTomorrow(chat_id=message.chat.id)

