import pickle
import os.path
import time
import requests
import urllib.parse
import pytz
import json


def returnWeatherInfo(requestData):
    errorCode = 0
    if "coord" in requestData:
        coord = requestData["coord"]
        coord = findLocCoord(coord)
        coord = getTimeLatLon(coord)
        coord = getPlace(coord)
    elif "address" in requestData:
        coord = findLatLon(requestData["address"])
        if coord == -1:
            errorCode = -1  # No coordinates found
    else:
        print("No location given")
        errorCode = -2

    if 0 <= errorCode:
        weatherData, updateVal = checkNewData(coord)
        return [weatherData, coord, errorCode]
    else:
        return [0, "", errorCode]


def getTimeLatLon(coord):
    url = 'http://api.geonames.org/timezoneJSON?formatted=true&lat={}&lng={}&username=gbweatherbot'.format(
        coord["lat"], coord["lon"])
    # tzWhere = tzwhere.tzwhere()
    # timezone_str = tzWhere.tzNameAt(float(coord["lat"]), float(coord["lon"]))
    #
    # dt = datetime.datetime.now(pytz.timezone(timezone_str))
    # time = dt.strftime("%H:%M")

    response = requests.get(url).json()
    if "time" in response:
        timeStr = response["time"]
        time = timeStr[-5:]
    else:
        time = "??:??"

    coord["time"] = time
    return coord

def getPlace(coord):
    url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat={}&lon={}'.format(
        coord["lat"], coord["lon"])

    response = requests.get(url).json()
    if "address" in response:
        address = response["address"]
        if "suburb" in address:
            place = address["suburb"]
        elif "city_district" in address:
            place = address["city_district"]
        elif "town" in address:
            place = address["town"]
        elif "county" in address:
            place = address["county"]
        else:
            place = "No matching address field"
    else:
        place = "No location found"

    coord["place"] = place
    return coord


def findLatLon(address):
    url = 'https://nominatim.openstreetmap.org/search?q=' + \
          urllib.parse.quote(address) + '&format=json'

    response = requests.get(url).json()
    if "lat" in response[0]:
        lat = response[0]["lat"]
        lon = response[0]["lon"]
        display_name = response[0]["display_name"]
        display_name_s = display_name.split(", ")
        if 3 < len(display_name_s):
            loc = display_name_s[3]
        else:
            loc = display_name
        coord = {
            "lat": lat,
            "lon": lon,
            "loc": loc
        }
        coord = getTimeLatLon(coord)
        coord = getPlace(coord)
        return coord
    else:
        return -1

def findLocCoord(coord):
    lat = coord["lat"]
    lon = coord["lon"]
    url = 'https://nominatim.openstreetmap.org/search?q=' + \
          urllib.parse.quote(str(lat)+","+str(lon)) + '&format=json'
    # print('findLocCoord\n'+url)

    response = requests.get(url).json()
    # print(json.dumps(response))
    if "lat" in response[0]:
        display_name = response[0]["display_name"]
        display_name_s = display_name.split(", ")
        if 3 < len(display_name_s):
            loc = display_name_s[3]
        else:
            loc = display_name
        coord["loc"] = loc
    else:
        coord["loc"] = "No location found"
    return coord



def checkNewData(coord):
    # If there has been new data within the last n minutes don't renew, else get and save
    returnVal = 0
    if os.path.isfile("weatherData"):
        returnVal = 1
        data = pickle.load(open("weatherData", "rb"))
        tNow = int(time.time())
        tLast = data["tLast"]
        if 60*5 < (tNow - tLast) or data['lat'] != coord['lat'] or\
            data['lon'] != coord['lon']:  # only get new data every 5 mins or if new data arrives
            returnVal = 2
            print("new data is acquired")
            data = getNewData(coord)
            pickle.dump(data, open("weatherData", "wb"))
        if False:
            if coord[0] != data["lat"] or coord[1] != data["lon"]:
                returnVal = 3
                print("Geodata has changed, new data is acquired")
                data = getNewData(coord)
                pickle.dump(data, open("weatherData", "wb"))

    else:
        data = getNewData(coord)
        print("old data used")
        pickle.dump(data, open("weatherData", "wb"))
    return [data, returnVal]



def getNewData(coord):
    api_key = os.environ["OWMAPI"]  # added through heroku config:add TOKEN=…
    # oneCall API
    base_url = "https://api.openweathermap.org/data/2.5/onecall?lat="
    lat = coord["lat"]
    lon = coord["lon"]
    complete_url = base_url + str(lat) + "&lon=" + str(lon) + \
                   "&units=metric&lang=de" + \
                   "&appid=" + api_key

    response = requests.get(complete_url)
    data = response.json()

    dTime = data["timezone_offset"]

    if "minutely" in data:
        for minD in data["minutely"]:
            minD["dt"] += dTime
    else:
        minDat = [{'dt': data["hourly"][0]["dt"], 'precipitation': 0}] * 61
        data["minutely"] = minDat
        for idx in range(0, len(data["minutely"])):
            data["minutely"][idx]["dt"] += dTime + (idx * 60)


    for hrlD in data["hourly"]:
        hrlD["dt"] += dTime

    if "alerts" in data:
        for alert in data["alerts"]:
            alert["start"] += dTime
            alert["end"] += dTime

    tNow = int(time.time())
    data["tLast"] = tNow
    return data
