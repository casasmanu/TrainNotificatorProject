import requests
import json
import datetime

#Station Monitor

#DONA - 8000078
#Pasing - 8004158

headers = {'Accept': 'application/json'}
params = {'when': 'today 5pm', 'nationalExpress': 'True','national': 'false','bus':'false','regional':'false', 'pretty': 'true','results':'10'}
station_id="8000078"
r = requests.get('https://v6.db.transport.rest/stops/'+station_id+'/departures?',params=params, headers=headers)

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
    dateActualDate=datetime.datetime.strptime(departure['when'][:-6],"%Y-%m-%dT%H:%M:%S")
    ActualDate=datetime.datetime.strftime(dateActualDate,"%H:%M:%S")
    datePlannedDate=datetime.datetime.strptime(departure['plannedWhen'][:-6],"%Y-%m-%dT%H:%M:%S")
    PlannedDate=datetime.datetime.strftime(datePlannedDate,"%H:%M:%S")
    departureImportantData=[TrainName,Destination,ActualDate,PlannedDate,]
    bahnhof.append(departureImportantData)
    print (departureImportantData)





print("done")