from weatherReader import returnWeatherInfo
from weatherMinutely import minutely
from weatherHourly import hourly
from weatherAlerts import alerts

def returnMinutely(requestData):
    weatherData, coord, errorCode = returnWeatherInfo(requestData)
    if 0 <= errorCode:
        plotTitle = coord["place"] + ", " + coord["time"]
        fileName, [rainStr, bikeStr] = minutely(weatherData["minutely"],plotTitle)
        fileName2, [minStr, hrlStr] = hourly(weatherData["hourly"], plotTitle)

        returnStr = rainStr + "\n" + bikeStr

        if minStr != "":
            returnStr += "\n" + minStr

        if "alerts" in weatherData:
            alertStr = alerts(weatherData["alerts"])
            returnStr += "\n" + alertStr

        return returnStr, fileName, errorCode
    else:
        return "", "", errorCode

def returnHourly(requestData):
    weatherData, coord, errorCode = returnWeatherInfo(requestData)
    if 0 <= errorCode:
        plotTitle = coord["place"] + ", " + coord["time"]
        fileName, [minStr, hrlStr] = hourly(weatherData["hourly"], plotTitle)
        if hrlStr == 0:
            returnStr = ""
        else:
            returnStr = hrlStr

        if "alerts" in weatherData:
            alertStr = alerts(weatherData["alerts"])
            returnStr += "\n" + alertStr

        return returnStr, fileName, errorCode
    else:
        return "", "", errorCode

def returnMinutelyHourly(requestData):
    weatherData, coord, errorCode = returnWeatherInfo(requestData)
    if 0 <= errorCode:
        plotTitle = coord["place"] + ", " + coord["time"]
        fileName, [rainStr, bikeStr] = minutely(weatherData["minutely"], plotTitle)
        fileName2, [minStr, hrlStr] = hourly(weatherData["hourly"], plotTitle)
        returnStr = rainStr
        if hrlStr != "":
            returnStr += "\n" + hrlStr

        if "alerts" in weatherData:
            alertStr = alerts(weatherData["alerts"])
            returnStr += "\n" + alertStr

        return returnStr, [fileName, fileName2], errorCode
    else:
        return "", "", errorCode