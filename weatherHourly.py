import matplotlib.pyplot as plt
import time
from datetime import datetime


def hourly(hrlyData, plotTitle):
    hourly = getHourly(hrlyData)
    returnStr = evalHourly(hourly)
    hour, min = map(int, time.strftime("%H %M").split())
    fileName = "hrl_" + str(hour) + "_" + str(min)
    plotHourlyPrec(hourly, fileName, plotTitle)
    return fileName, returnStr


def plotHourlyPrec(hourly, fileName, plotTitle):
    dt = hourly["dt"]
    temp = hourly["temp"]
    feels_like = hourly["feels_like"]
    dt_zero = [t - dt[0] for t in dt]
    hours = [t / 3600 for t in dt_zero]
    # TODO: Add real time for x axis
    # Seems to have sorted itself out...

    dt_text = [datetime.fromtimestamp(t).strftime("%H:%M") for t in dt]

    dt_labelText = [dt_text[idx] for idx in range(0, 25, 6)] #  Alternativ: 0,48,8
    #dt_labelText.append("")
    dt_labelTicks = [hours[idx] for idx in range(0, 25, 6)]
    #dt_labelTicks.append(48)

    fig = plt.figure()

    if any([r != 0 for r in hourly["rain"]]) or any([s != 0 for s in hourly["snow"]]):
        rain = hourly["rain"]
        snow = hourly["snow"]
        ax = plt.gca()
        ax2 = ax.twinx()
        if any([r != 0 for r in rain[0:24]]):
            ax.bar(hours[0:24], rain[0:24], label="Regen")
        if any([s != 0 for s in snow[0:24]]):
            ax.bar(hours[0:24], snow[0:24], color="darkgray", label="Schnee")
        #ax.fill_between(hours, prec)
        ax.set_yticks([0.3, 2, 7])
        ax.set_yticklabels(["leicht", "mittel", "stark"])
        ax.set_ylabel("Niederschlag [mm]")
        if max(rain) < 10:
            ax.set_ylim(0, 10)
    else:
        ax2 = plt.gca()

    ax2.plot(hours[0:24], temp[0:24], 'r', label="Temperatur")
    ax2.plot(hours[0:24], feels_like[0:24], 'g', label="Gefühlt wie")
    fig.legend(loc="upper right")
    ax2.set_xlabel("Zeit [h]")
    ax2.set_ylabel("Temperatur [" + chr(176) + "C]")
    minT, maxT = ax2.get_ylim()
    ax2.set_ylim(min(0, minT), maxT)

    plt.title("Wetter in " + plotTitle)

    ax2.set_xticks(dt_labelTicks)
    ax2.set_xticklabels(dt_labelText)

    plt.show(block=False)
    #print(max(prec))

    plt.savefig(fileName + ".jpg")
    # Image.open(fileName + ".png").save(fileName + '.jpg', 'JPEG')
    plt.close()


def evalHourly(hourly):
    snow = hourly["snow"]
    minStr = ""
    if any([s != 0 for s in snow[0:2]]):
        minStr = "Es wird voraussichtlich schneien."
        hrlStr = "Schnee in den nächsten 2 h."
    elif any([s != 0 for s in snow[0:4]]):
        hrlStr = "Schnee in den nächsten 4 h."
    elif any([s != 0 for s in snow[0:8]]):
        hrlStr = "Schnee in den nächsten 8 h."
    elif any([s != 0 for s in snow[0:24]]):
        hrlStr = "Schnee in den nächsten 24 h."
    elif any([s != 0 for s in snow]):
        hrlStr = "Schnee in den nächsten 48 h."
    else:
        hrlStr = ""
    return [minStr, hrlStr]


def getHourly(hrlData):
    # requires ["hourly"] key from base data set
    dt = [d["dt"] for d in hrlData]
    temp = [d["temp"] for d in hrlData]
    feels_like = [d["feels_like"] for d in hrlData]
    rain = [h["rain"]["1h"] if "rain" in h else 0 for h in hrlData]
    snow = [h["snow"]["1h"] if "snow" in h else 0 for h in hrlData]
    hourly = {"dt": dt,
              "temp": temp,
              "feels_like": feels_like,
              "rain": rain,
              "snow": snow}
    return hourly
