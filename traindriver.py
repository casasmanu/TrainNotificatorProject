import requests
import json
import datetime

#Station Monitor

#DONA - 8000078
#Pasing - 8004158
#Munchen - 8000261

def retrieveDepartures(station_id=8000078,desiredDate='yesterday 5pm'):
    
    headers = {'Accept': 'application/json'}

    params = {'when': desiredDate,
                'duration':30,
                'nationalExpress': 'True',
                'national': 'True',
                'bus':'False',
                'regional':'True',
                'regionalExpress':'False',
                'pretty': 'True',
                'suburban':'False',
                'taxi':'False',
                'results':10}

    r = requests.get('https://v6.db.transport.rest/stops/'+str(station_id)+'/departures?',params=params, headers=headers,timeout=5)

    myjson=json.loads(r.text)

    # Destination---- myjson['departures'][0]['destination']['name']
    # Train         - myjson['departures'][0]['line']['name']
    # When          - myjson['departures'][0]['when']
    # Planned       - myjson['departures'][0]['plannedWhen']
    # myjson['departures']

    bahnhof=[]

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
            # myjson['departures'][0]['cancelled']
            delayTime=departure['when'][-6:]
            ActualDate=datetime.datetime.strftime(dateActualDate,"%H:%M:%S")
            Platform=departure['platform']
            departureImportantData=[TrainName,Destination,PlannedDate,ActualDate+delayTime,Platform]
            bahnhof.append(departureImportantData)
    
        print (departureImportantData)




retrieveDepartures()