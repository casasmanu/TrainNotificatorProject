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
#Augsburg

def retrieveDepartures(station_id=8000078,desiredDate='yesterday 5pm',service="regional",value=True):
    
    bahnhof=[]
    try:    
        headers = {'Accept': 'application/json'}

        params = {'when': desiredDate,
                'duration':30,
                'nationalExpress': False,
                'national': False,
                'regionalExpress':False,
                'regional':False,
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

        logger.info("dividing departures and taking only important data")
        for departure in myjson['departures']:
            TrainName= departure['line']['name']
            Destination= departure['destination']['name']
            datePlannedDate=datetime.datetime.strptime(departure['plannedWhen'][:-9],"%Y-%m-%dT%H:%M")
            PlannedDate=datetime.datetime.strftime(datePlannedDate,"%H:%M")
                
            if dict.__contains__(departure,'cancelled'):

                departureImportantData=[TrainName,Destination,PlannedDate,"CANCELADO"]
                bahnhof.append(departureImportantData)

            else:
                dateActualDate=datetime.datetime.strptime(departure['when'][:-9],"%Y-%m-%dT%H:%M")
                delayTime=departure['when'][-6:]
                ActualDate=datetime.datetime.strftime(dateActualDate,"%H:%M")
                Platform=departure['platform']
                departureImportantData=[TrainName,
                                        "| Destination "+Destination,
                                        "| Planned "+PlannedDate,
                                        "| Actual Time "+ActualDate+delayTime[:-3]
                                        ,"| Gleis "+Platform]
                bahnhof.append(departureImportantData)
        
            #print (departureImportantData)
    except Exception as e:
        logger.error(e)
        bahnhof.append("Error while trying to retrieve station data")
        logger.error("error while trying to retrieve station data")
    
    outputString=""
    for i in bahnhof:
        string = " ".join(i)
        outputString+=string + " \n\n"

    logger.info("Send message via TELEGRAM")
    print(outputString)
    bot_send_msg(outputString)

#https://v6.db.transport.rest/journeys?

def journeyPlanner(origin=8004158,destination=8000078,when='tomorrow 6:50am'):
    try:    
        headers = {'Accept': 'application/json'}

        params = {'departure': when,
                'from':origin,
                'to':destination,
                'via':8000013,
                'nationalExpress': True,
                'national': True,
                'regionalExpress':True,
                'regional':True,
                'suburban':False,
                'bus':False,
                'subway':False,
                'tram':False,
                'taxi':False}
        
        #params[service]=value
        logger.info("calling API")
        r = requests.get('https://v6.db.transport.rest/journeys?',params=params, headers=headers,timeout=5)

        myjson=json.loads(r.text)
        
        #myjson['journeys'][0]['legs'][0]['departure']
        #myjson['journeys'][0]['legs'][0]['arrival']
        #myjson['journeys'][0]['legs'][0]['plannedDeparturePlatform']
        #myjson['journeys'][0]['legs'][0]['line']['name']
        
        fahrt=[]
        ICEtripFound=False
        description="NO AVAILABLE TRAIN FOUNDED OR PROBLEM"
        PlannedDate=""
        platform=""
        
        for journey in myjson['journeys']:
            trainName= journey['legs'][0]['line']['name']   #'ICE 802'
            if trainName=='ICE 802':
                description="ICE 802 founded, please check data below \n"
                datePlannedDate=datetime.datetime.strptime(journey['legs'][0]['plannedDeparture'][:-9],"%Y-%m-%dT%H:%M")
                PlannedDate=" Time: "+datetime.datetime.strftime(datePlannedDate,"%H:%M")
                platform=" | Platform: " + journey['legs'][0]['plannedDeparturePlatform']
                break
            elif(trainName=='RB 87'):
                description="ACHTUNG! RB 87 founded, check trip and leave home EARLY \n"
                datePlannedDate=datetime.datetime.strptime(journey['legs'][0]['plannedDeparture'][:-9],"%Y-%m-%dT%H:%M")
                PlannedDate=" Time: "+datetime.datetime.strftime(datePlannedDate,"%H:%M")
                platform=" | Platform: " + journey['legs'][0]['plannedDeparturePlatform']
                break
            
        strfahrt=description + PlannedDate+ platform
            
        print(strfahrt)
    except Exception as e:
        print(e)
        strfahrt="error while calling API, please check manually"
        
    bot_send_msg(strfahrt)
    
    
#journeyPlanner()