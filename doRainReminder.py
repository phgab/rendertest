import telepot
import os
from weatherFuncts import returnMinutely

TOKEN = os.environ["TELTOKEN"]


def main():
    bot = telepot.Bot(TOKEN)

    returnStr, fileName, errorCode = returnMinutely({"address": "Kriegerstrasse 22, Hannover"})
    bot.sendPhoto(532298931, open(fileName + ".jpg", 'rb'))
    bot.sendMessage(532298931, returnStr)


if __name__ == '__main__':
    main()
