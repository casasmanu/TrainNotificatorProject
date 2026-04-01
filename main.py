import schedule
import time
import os
from dotenv import load_dotenv
import logging
from traindriver import retrieveDepartures,journeyPlanner
from Drivers.drvWeather import getWeatherToday, getWeatherTomorrow, getWeeklySummary, checkRainSnowAlert
from Drivers.drvTelegram import poll_weather_commands

# Load the .env file
load_dotenv()
logger = logging.getLogger(__name__)

import Drivers.drvLogger as drvLogger
drvLogger.initLogger()

try:
    botToken = os.environ['BOT_TOKEN']
    destinatary = os.environ['BOT_DESTINATARY']
    logger.info("Main.py - environment variables loaded")
except KeyError:
    botToken = None
    destinatary = None
    logger.error("Main.py - Error while loading init variables from .env")

# Station IDs: DONA=8000078, Pasing=8004158, München Hbf=8000261

def main():
    schedule.every().day.at("06:30").do(
        retrieveDepartures,station_id=8004158,desiredDate="7am")
    
    schedule.every().day.at("06:30").do(
        getWeatherToday)
    
    schedule.every().day.at("16:30").do(
        retrieveDepartures,station_id=8000078,desiredDate="5pm")
    
    schedule.every().day.at("22:00").do(
        journeyPlanner,origin=8000261,destination=8000078,when="tomorrow 7am",preferred_train="ICE 802")
    
    schedule.every().day.at("22:00").do(
        getWeatherTomorrow)

    # Rain/snow alert: checks next 4 days, sends message only if precipitation expected
    schedule.every().day.at("18:00").do(
        checkRainSnowAlert)

    # Weekly summary every Sunday at 18:05
    schedule.every().sunday.at("18:05").do(
        getWeeklySummary)

    while True:
        poll_weather_commands()
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    main()
