import requests
import json
import datetime
import logging
import time
from Drivers.drvTelegram import bot_send_msg
# ----------------------- Variables ----------------------- #
logger = logging.getLogger(__name__)


def _format_api_time(value):
    if not value:
        return "N/A"
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M")
    except ValueError:
        return value


def _request_with_retry(url, params, headers, timeout=12, retries=3, backoff_seconds=1.5):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            retryable_statuses = {429, 500, 502, 503, 504}
            if response.status_code in retryable_statuses and attempt < retries:
                logger.warning(f"API temporary error {response.status_code}, retry {attempt}/{retries}")
                time.sleep(backoff_seconds * attempt)
                continue
            return response
        except (requests.Timeout, requests.ConnectionError) as request_error:
            last_error = request_error
            if attempt < retries:
                logger.warning(f"API timeout/connection issue, retry {attempt}/{retries}")
                time.sleep(backoff_seconds * attempt)
                continue
            raise
    if last_error:
        raise last_error
    raise Exception("API request failed after retries")

#Station Monitor

#DONA - 8000078
#Pasing - 8004158
#Munchen - 8000261
#Augsburg

def retrieveDepartures(station_id=8000078, desiredDate='yesterday 5pm', service=None, value=True):
    
    bahnhof=[]
    try:    
        headers = {'Accept': 'application/json'}

        params = {'when': desiredDate,
                'duration': 30,
                'nationalExpress': True,
                'national': True,
                'regionalExpress': True,
                'regional': True,
                'suburban': True,
                'bus': True,
                'subway': True,
                'tram': True,
                'taxi': True,
                'pretty': True,
                'results': 10}

        if service in params:
            for key in ('nationalExpress', 'national', 'regionalExpress', 'regional', 'suburban', 'bus', 'subway', 'tram', 'taxi'):
                params[key] = False
            params[service] = value
        
        logger.info("calling API")
        r = _request_with_retry(
            'https://v6.db.transport.rest/stops/'+str(station_id)+'/departures?',
            params=params,
            headers=headers,
            timeout=12,
            retries=8,
            backoff_seconds=2,
        )

        if r.status_code != 200:
            raise Exception(f"API returned status {r.status_code}: {r.text}")

        myjson=json.loads(r.text)
        
        if myjson is None:
            raise Exception("API returned null")
        
        if 'departures' not in myjson:
            raise Exception(f"API response missing 'departures' key: {myjson}")

        logger.info("dividing departures and taking only important data")
        departures = myjson.get('departures') or []
        for departure in departures:
            line = departure.get('line') or {}
            train_name = line.get('name', 'Unknown')

            destination_data = departure.get('destination')
            if isinstance(destination_data, dict):
                destination = destination_data.get('name', 'Unknown')
            else:
                destination = destination_data or 'Unknown'

            planned_date = _format_api_time(departure.get('plannedWhen'))

            if departure.get('cancelled', False):
                departure_important_data = [train_name, destination, planned_date, 'CANCELADO']
                bahnhof.append(departure_important_data)
            else:
                actual_date = _format_api_time(departure.get('when'))
                platform = str(departure.get('platform') or 'N/A')
                departure_important_data = [
                    train_name,
                    '| Destination ' + destination,
                    '| Planned ' + planned_date,
                    '| Actual Time ' + actual_date,
                    '| Gleis ' + platform,
                ]
                bahnhof.append(departure_important_data)
        
            #print (departureImportantData)
    except Exception as e:
        logger.exception(f"retrieveDepartures failed after retries: {e}")
        return
    
    outputString=""
    for i in bahnhof:
        if isinstance(i, list):
            string = " ".join(i)
        else:
            string = str(i)
        outputString+=string + " \n\n"

    if not outputString.strip():
        outputString = "No departures available at this time."

    logger.info("Send message via TELEGRAM")
    print(outputString)
    bot_send_msg(outputString)

#https://v6.db.transport.rest/journeys?

def journeyPlanner(origin=8004158,destination=8000078,when='tomorrow 6:50am',preferred_train='ICE 802'):
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
        r = _request_with_retry(
            'https://v6.db.transport.rest/journeys?',
            params=params,
            headers=headers,
            timeout=12,
            retries=8,
            backoff_seconds=2,
        )

        if r.status_code != 200:
            raise Exception(f"API returned status {r.status_code}: {r.text}")

        myjson=json.loads(r.text)
        
        if myjson is None:
            raise Exception("API returned null")
        
        if 'journeys' not in myjson:
            raise Exception(f"API response missing 'journeys' key: {myjson}")
        
        #myjson['journeys'][0]['legs'][0]['departure']
        #myjson['journeys'][0]['legs'][0]['arrival']
        #myjson['journeys'][0]['legs'][0]['plannedDeparturePlatform']
        #myjson['journeys'][0]['legs'][0]['line']['name']
        
        strfahrt = "No journey information available."
        found_preferred = False

        for journey in myjson.get('journeys', []):
            legs = journey.get('legs') or []
            for leg in legs:
                line = leg.get('line') or {}
                train_name = line.get('name', '')
                if train_name == preferred_train:
                    planned = _format_api_time(leg.get('plannedDeparture') or leg.get('departure'))
                    platform = str(leg.get('plannedDeparturePlatform') or leg.get('departurePlatform') or 'N/A')
                    strfahrt = f"{preferred_train} found for {when}. Time: {planned} | Platform: {platform}"
                    found_preferred = True
                    break
            if found_preferred:
                break

        if strfahrt == "No journey information available.":
            for journey in myjson.get('journeys', []):
                legs = journey.get('legs') or []
                if not legs:
                    continue
                first_leg = legs[0]
                line = first_leg.get('line') or {}
                train_name = line.get('name', 'Unknown')
                planned = _format_api_time(first_leg.get('plannedDeparture') or first_leg.get('departure'))
                platform = str(first_leg.get('plannedDeparturePlatform') or first_leg.get('departurePlatform') or 'N/A')
                strfahrt = f"{preferred_train} not found. Next option: {train_name} at {planned} | Platform: {platform}"
                break
            
        print(strfahrt)
    except requests.Timeout:
        logger.error("journeyPlanner timeout while calling API")
        return
    except Exception as e:
        logger.exception(f"journeyPlanner failed: {e}")
        return
        
    if not strfahrt.strip():
        strfahrt = "No journey information available."

    bot_send_msg(strfahrt)
    
    
#journeyPlanner()