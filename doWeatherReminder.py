import telepot
import os
from weatherFuncts import returnMinutelyHourly

TOKEN = os.environ["TELE_BOT"]


def main():
    bot = telepot.Bot(TOKEN)

    returnStr, [fileNameMin, fileNameHrl], errorCode1 = returnMinutelyHourly({"address": "Slicherstr 6, Hannover"})

    bot.sendPhoto(532298931, open(fileNameHrl + ".jpg", 'rb'))
    bot.sendPhoto(532298931, open(fileNameMin + ".jpg", 'rb'))
    bot.sendMessage(532298931, returnStr)


if __name__ == '__main__':
    main()
