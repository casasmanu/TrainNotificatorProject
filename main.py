import schedule
import time
import os
from dotenv import load_dotenv
import logging
from traindriver import retrieveDepartures,journeyPlanner

# ----------------------------Global variables ------------------------------_#
global botToken,destinatary

# Load the .env file
load_dotenv()
logger = logging.getLogger(__name__)

#from Drivers.drvConfig import readConfigFile

import Drivers.drvLogger as drvLogger


drvLogger.initLogger()
### read config File
try:
    botToken = os.environ['BOT_TOKEN']
    destinatary=os.environ['BOT_DESTINATARY']
    logger.info("Main.py - environment variables loaded")  
except:
    logger.error("Main.py - Error while loading init variables from .env")

#retrieveDepartures(station_id=8004158,desiredDate="tomorrow 7am")
#journeyPlanner()

def main():
    #DONA - 8000078
    #Pasing - 8004158
    #Munchen - 8000261
    # Programa las llamadas a las funciones en intervalos diferentes
    schedule.every().day.at("06:30").do(
        retrieveDepartures,station_id=8004158,desiredDate="7am")
    
    schedule.every().day.at("16:30").do(
        retrieveDepartures,station_id=8000078,desiredDate="5pm")
    
    schedule.every().day.at("22:00").do(
        journeyPlanner,origin=8000261,destination=8000078,when="tomorrow 7am")
    
    schedule.every().day.at("23:00").do(
        retrieveDepartures,station_id=8000261,desiredDate="tomorrow 7am")
    
    while True:
        schedule.run_pending()
        time.sleep(5)

if __name__ == "__main__":
    main()
