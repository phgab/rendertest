
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from weatherFuncts import returnMinutelyHourly

FIRST, SECOND, THIRD = range(3)
ENTERLOC, FIXEDLOC, USERLOC = range(3)
fixedAdr = [["Kriegerstrasse 22",", 30161 Hannover"],
            ["Stadtfelddamm 34", ", 30625 Hannover"],
            ["Wiedenthaler Sand 9", ", 21147 Hamburg"],
            ["An der Hasenkuhle 7", ", 21224 Rosengarten"]]

def getConvHandlerWeather():
    convHandlerWeather = ConversationHandler(
        entry_points=[CommandHandler("wetter", weatherLocChoice)],
        states={
            FIRST: [CallbackQueryHandler(enterLoc, pattern='^' + str(ENTERLOC) + '$'),
                    CallbackQueryHandler(fixedLoc, pattern='^' + str(FIXEDLOC) + '$'),
                    CallbackQueryHandler(userLoc, pattern='^' + str(USERLOC) + '$')
                ],
            SECOND: [MessageHandler(filters.LOCATION, readLoc),
                     MessageHandler(filters.text, readAddress),
                     CallbackQueryHandler(evalSelectedAddress)
                ],
            },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerWeather


def weatherLocChoice(update, context):
    keyboard = [[InlineKeyboardButton("Adresse eingeben", callback_data=str(ENTERLOC))],
                [InlineKeyboardButton("Auswahl", callback_data=str(FIXEDLOC))],
                [InlineKeyboardButton("Eigener Standort", callback_data=str(USERLOC))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
    return FIRST


def enterLoc(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Bitte die Adresse inkl. PLZ und Ort senden.")
    return SECOND


def fixedLoc(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton(fixedAdr[0][0], callback_data="0"),
                InlineKeyboardButton(fixedAdr[1][0], callback_data="1")],
                [InlineKeyboardButton(fixedAdr[2][0], callback_data="2"),
                InlineKeyboardButton(fixedAdr[3][0], callback_data="3")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text="Welche Adresse?:", reply_markup=reply_markup)
    return SECOND


def userLoc(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="Bitte den Standort teilen (Büroklammer -> Standort)")
    return SECOND


def readLoc(update, context):
    bot = context.bot
    bot.sendMessage(532298931, "loc")
    user_location = update.message.location
    lat = user_location.latitude
    lon = user_location.longitude
    coord = {"lat": lat, "lon": lon}

    returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"coord": coord})
    if errorCode == -2:
        bot.sendMessage(update.message.chat.id, "Keine Koordinaten übermittelt")
    else:
        bot.send_photo(update.message.chat.id, open(fileNameHrl + ".jpg", 'rb'))
        bot.send_photo(update.message.chat.id, open(fileNameMin + ".jpg", 'rb'))
        update.message.reply_text(returnStr)
    return ConversationHandler.END


def readAddress(update, context):
    bot = context.bot
    address = update.message.text
    update.message.reply_text(address)

    returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"address": address})
    if errorCode == -2:
        bot.sendMessage(update.message.chat.id, "Keine Adresse übermittelt")
    elif errorCode == -1:
        bot.sendMessage(update.message.chat.id, "Adresse konnte nicht gefunden werden")
    else:
        bot.send_photo(update.message.chat.id, open(fileNameHrl + ".jpg", 'rb'))
        bot.send_photo(update.message.chat.id, open(fileNameMin + ".jpg", 'rb'))
        update.message.reply_text(returnStr)
    return ConversationHandler.END


def evalSelectedAddress(update, context):
    query = update.callback_query
    query.answer()
    bot = query.bot
    qData = query.data
    adID = int(qData)
    address = fixedAdr[adID][0] + fixedAdr[adID][1]

    returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"address": address})
    if errorCode == -2:
        bot.sendMessage(query.message.chat.id, "Keine Adresse übermittelt")
    elif errorCode == -1:
        bot.sendMessage(query.message.chat.id, "Adresse konnte nicht gefunden werden")
    else:
        bot.send_photo(query.message.chat.id, open(fileNameHrl + ".jpg", 'rb'))
        bot.send_photo(query.message.chat.id, open(fileNameMin + ".jpg", 'rb'))
        bot.sendMessage(query.message.chat.id, returnStr)
    return ConversationHandler.END

def cancel(update, context):
    #user = update.message.from_user
    #logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Okay dann halt nicht -.-')

    return ConversationHandler.END