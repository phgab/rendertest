import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from actUserDataHandling import getUserData

FIRST, SECOND, THIRD = range(3)
L1, L2, L3 = range(3)
CA, CB, CC, BACK = range(4)

# 1. a. Fahrradadressen bearbeiten, b. Wettervorherasge-Adressen bearbeiten (jeweils Kurzname und Adresse eintragen)
# 2. (jeweils): a. Adresse hinzufügen, b. Adressen bearbeiten, c. Adresse löschen
# Bei a. und b. jeweils Feedback über die ermittelte Adresse

def getConvHandlerSettings():
    convHandlerSettings = ConversationHandler(
        entry_points=[CommandHandler("einstellungen", settingsFirstLayer)],
        states={
            L1: [CallbackQueryHandler(settingsFirstLayer)],
            L2: [CallbackQueryHandler(settingsSecondLayer_bike, pattern='^' + str(CA) + '$'),
                 CallbackQueryHandler(settingsSecondLayer_weather, pattern='^' + str(CB) + '$')],
            L3: [],
            SECOND: [MessageHandler(filters.LOCATION, readLoc),
                     MessageHandler(filters.TEXT, readAddress),
                     CallbackQueryHandler(evalSelectedAddress)],
            },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerSettings

async def settingsFirstLayer(update, context):
    keyboard = [[InlineKeyboardButton("Fahrrad-Adressen bearbeiten", callback_data=str(CA))],
                [InlineKeyboardButton("Wettervorhersage-Adressen bearbeiten", callback_data=str(CB))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
    return L2

def getSecondLayerKeyboard():
    keyboard = [[InlineKeyboardButton("Adresse hinzufügen", callback_data=str(CA))],
                [InlineKeyboardButton("Adressen bearbeiten", callback_data=str(CB))],
                [InlineKeyboardButton("Adresse löschen", callback_data=str(CC))],
                [InlineKeyboardButton("Zurück", callback_data=str(BACK))]]
    return keyboard

async def settingsSecondLayer_bike(update, context):
    context.user_data['L1'] = 'bike'
    keyboard = getSecondLayerKeyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Aktion für Fahrrad-Adressen wählen:', reply_markup=reply_markup)
    return L3

async def settingsSecondLayer_weather(update, context):
    context.user_data['L1'] = 'weather'
    keyboard = getSecondLayerKeyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Aktion für Wettervorhersage-Adressen wählen:', reply_markup=reply_markup)
    return L3

async def listUserAddresses(chatId):
    t=0

async def addAddress(update, context):
    t=0

async def addShortName(update, context):
    t=0

async def confirmAddition(update, context):
    t=0

async def selectAddress(update, context):
    t=0
    # change or delete from L2 context

async def modifyAddress(update, context):
    t=0

async def modifyShortName(update, context):
    t=0

async def confirmModification(update, context):
    t=0

async def confirmDeletion(update, context):
    t=0

async def finalMessage(update, context):
    t=0

async def cancel(update, context):
    t=0



# async def weatherLocChoice(update, context):
#     keyboard = [[InlineKeyboardButton("Adresse eingeben", callback_data=str(ENTERLOC))],
#                 [InlineKeyboardButton("Auswahl", callback_data=str(FIXEDLOC))],
#                 [InlineKeyboardButton("Eigener Standort", callback_data=str(USERLOC))]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
#     return FIRST


async def enterLoc(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Bitte die Adresse inkl. PLZ und Ort senden.")
    return SECOND


async def fixedLoc(update, context):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(fixedAdr[0][0], callback_data="0"),
                InlineKeyboardButton(fixedAdr[1][0], callback_data="1")],
                [InlineKeyboardButton(fixedAdr[2][0], callback_data="2"),
                InlineKeyboardButton(fixedAdr[3][0], callback_data="3")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Welche Adresse?:", reply_markup=reply_markup)
    return SECOND


async def userLoc(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Bitte den Standort teilen (Büroklammer -> Standort)")
    return SECOND


async def readLoc(update, context):
    bot = context.bot
    await bot.sendMessage(context.bot_data["admin_chat_id"], "loc")
    user_location = update.message.location
    lat = user_location.latitude
    lon = user_location.longitude
    coord = {"lat": lat, "lon": lon}

    returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"coord": coord})
    if errorCode == -2:
        await bot.sendMessage(update.message.chat.id, "Keine Koordinaten übermittelt")
    else:
        await bot.send_photo(update.message.chat.id, open(fileNameHrl + ".jpg", 'rb'))
        await bot.send_photo(update.message.chat.id, open(fileNameMin + ".jpg", 'rb'))
        await update.message.reply_text(returnStr)
    return ConversationHandler.END


async def readAddress(update, context):
    bot = context.bot
    address = update.message.text
    await update.message.reply_text(address)

    returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"address": address})
    if errorCode == -2:
        await bot.sendMessage(update.message.chat.id, "Keine Adresse übermittelt")
    elif errorCode == -1:
        await bot.sendMessage(update.message.chat.id, "Adresse konnte nicht gefunden werden")
    else:
        await bot.send_photo(update.message.chat.id, open(fileNameHrl + ".jpg", 'rb'))
        await bot.send_photo(update.message.chat.id, open(fileNameMin + ".jpg", 'rb'))
        await update.message.reply_text(returnStr)
    return ConversationHandler.END


async def evalSelectedAddress(update, context):
    query = update.callback_query
    await query.answer()
    bot = context.bot
    qData = query.data
    adID = int(qData)
    address = fixedAdr[adID][0] + fixedAdr[adID][1]

    returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"address": address})
    if errorCode == -2:
        await bot.sendMessage(query.message.chat.id, "Keine Adresse übermittelt")
    elif errorCode == -1:
        await bot.sendMessage(query.message.chat.id, "Adresse konnte nicht gefunden werden")
    else:
        await bot.send_photo(query.message.chat.id, open(fileNameHrl + ".jpg", 'rb'))
        await bot.send_photo(query.message.chat.id, open(fileNameMin + ".jpg", 'rb'))
        await bot.sendMessage(query.message.chat.id, returnStr)
    return ConversationHandler.END

# async def cancel(update, context):
#     #user = update.message.from_user
#     #logger.info("User %s canceled the conversation." % user.first_name)
#     await update.message.reply_text('Okay dann halt nicht -.-')
#
#     return ConversationHandler.END