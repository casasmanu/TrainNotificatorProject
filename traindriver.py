import requests
import json
import datetime
import logging
from Drivers.drvTelegram import bot_send_msg
# ----------------------- Variables ----------------------- #
logger = logging.getLogger(__name__)

#Station Monitor

#DONA - 8000078
#Pasing - 8004158
#Munchen - 8000261

def retrieveDepartures(station_id=8000078,desiredDate='yesterday 5pm',service="nationalExpress",value=True):
    
    bahnhof=[]
    try:    
        headers = {'Accept': 'application/json'}

        params = {'when': desiredDate,
                'duration':30,
                'nationalExpress': False,
                'national': True,
                'regionalExpress':False,
                'regional':True,
                'suburban':False,
                'bus':False,
                'subway':False,
                'tram':False,
                'taxi':False,
                'pretty': True,
                'results':10}
        
        params[service]=value
        logger.info("calling API")
        r = requests.get('https://v6.db.transport.rest/stops/'+str(station_id)+'/departures?',params=params, headers=headers,timeout=5)

        myjson=json.loads(r.text)

        logger("dividing departures and taking only important data")
        for departure in myjson['departures']:
            TrainName= departure['line']['name']
            Destination= departure['destination']['name']
            datePlannedDate=datetime.datetime.strptime(departure['plannedWhen'][:-6],"%Y-%m-%dT%H:%M:%S")
            PlannedDate=datetime.datetime.strftime(datePlannedDate,"%H:%M:%S")
                
            if dict.__contains__(departure,'cancelled'):

                departureImportantData=[TrainName,Destination,PlannedDate,"CANCELADO"]
                bahnhof.append(departureImportantData)

            else:
                dateActualDate=datetime.datetime.strptime(departure['when'][:-6],"%Y-%m-%dT%H:%M:%S")
                delayTime=departure['when'][-6:]
                ActualDate=datetime.datetime.strftime(dateActualDate,"%H:%M:%S")
                Platform=departure['platform']
                departureImportantData=[TrainName,Destination,PlannedDate,ActualDate+delayTime,Platform]
                bahnhof.append(departureImportantData)
        
            print (departureImportantData)
    except:
        bahnhof.append("Error while trying to retrieve station data")
        logger.error("error while trying to retrieve station data")
        
    logger.info("Send message via TELEGRAM")
    bot_send_msg(bahnhof)




#retrieveDepartures()