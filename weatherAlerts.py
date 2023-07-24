import time
from datetime import datetime


def alerts(alertData):
    alerts = getAlerts(alertData)
    numAlerts, returnStr = evalAlerts(alerts)
    if 0 < numAlerts:
        return returnStr
    else:
        return ""


def evalAlerts(alerts):
    numAlerts = 0
    alertStr = ""
    for event in alerts["event"]:
        if 0 < numAlerts:
            alertStr += "\n"
        startText = datetime.fromtimestamp(alerts["start"][numAlerts]).strftime("%H:%M")
        endText = datetime.fromtimestamp(alerts["end"][numAlerts]).strftime("%H:%M")
        sender_name = alerts["sender_name"][numAlerts]
        description = alerts["description"][numAlerts]

        numAlerts += 1

        alertStr += "Alert " + str(numAlerts) + ": "
        alertStr += event + " (" + startText + " - " + endText + ", " + sender_name + ")\n"
        alertStr += description

    if numAlerts == 1:
        returnStr = str(numAlerts) + " ALERT:" "\n" + alertStr
    else:
        returnStr = str(numAlerts) + " ALERTS:" "\n" + alertStr

    return numAlerts, returnStr


def getAlerts(alertData):
    # requires ["alerts"] key from base data set
    sender_name = [x["sender_name"] for x in alertData]
    event = [x["event"] for x in alertData]
    start = [x["start"] for x in alertData]
    end = [x["end"] for x in alertData]
    description = [x["description"] for x in alertData]

    alerts = {"sender_name": sender_name,
              "event": event,
              "start": start,
              "end": end,
              "description": description}
    return alerts
