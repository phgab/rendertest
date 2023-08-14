import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from weatherFuncts import returnMinutelyHourly
from actUserDataHandling import loadSingleUserData, getChatId

FIRST, SECOND, THIRD = range(3)
ENTERLOC, FIXEDLOC, USERLOC = range(3)

def getConvHandlerWeather():
    convHandlerWeather = ConversationHandler(
        entry_points=[CommandHandler("wetter", weatherLocChoice)],
        states={
            FIRST: [CallbackQueryHandler(enterLoc, pattern='^' + str(ENTERLOC) + '$'),
                    CallbackQueryHandler(fixedLoc, pattern='^' + str(FIXEDLOC) + '$'),
                    CallbackQueryHandler(userLoc, pattern='^' + str(USERLOC) + '$')
                    ],
            SECOND: [MessageHandler(filters.LOCATION & (~ filters.COMMAND), readLoc),
                     MessageHandler(filters.TEXT & (~ filters.COMMAND), readAddress),
                     CallbackQueryHandler(evalSelectedAddress)
                     ],
            },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerWeather


async def weatherLocChoice(update, context):
    keyboard = [[InlineKeyboardButton("Adresse eingeben", callback_data=str(ENTERLOC))],
                [InlineKeyboardButton("Auswahl", callback_data=str(FIXEDLOC))],
                [InlineKeyboardButton("Eigener Standort", callback_data=str(USERLOC))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
    return FIRST


async def enterLoc(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Bitte die Adresse inkl. PLZ und Ort senden.")
    return SECOND


async def fixedLoc(update, context):
    query = update.callback_query
    await query.answer()
    chatId = getChatId(update, context)
    userData = loadSingleUserData(chatId)
    if ('addresses' in userData and 'weather' in userData['addresses'] and
            0 < len(userData['addresses']['weather'])):
        addresses = userData['addresses']['weather']
        context.user_data['addresses'] = addresses
        keyboard = []
        numAdr = len(addresses)
        if 2 < numAdr:
            if (numAdr % 2) == 0:
                rng = range(int(numAdr/2))
            else:
                rng = range(int((numAdr - 1) / 2))
            for idx in rng:
                keyboard.append([InlineKeyboardButton(addresses[idx*2]['shortName'], callback_data=str(idx*2)),
                                 InlineKeyboardButton(addresses[idx*2 + 1]['shortName'], callback_data=str(idx*2 + 1))])
            if (numAdr % 2) == 1:
                keyboard.append([InlineKeyboardButton(addresses[numAdr-1]['shortName'], callback_data=str(numAdr-1))])
        else:
            for ctr, address in enumerate(addresses):
                keyboard.append([InlineKeyboardButton(address['shortName'], callback_data=str(ctr))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Welche Adresse?', reply_markup=reply_markup)
        return SECOND
    else:
        await query.edit_message_text('Es sind noch keine Wettervorhersage-Adressen gespeichert. ' +
                                        'Dies ist unter /einstellungen möglich.')
        return ConversationHandler.END

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
    addresses = context.user_data['addresses']
    if 'coord' in addresses[adID]:
        coord = addresses[adID]['coord']
        returnStr, [fileNameMin, fileNameHrl], errorCode = returnMinutelyHourly({"coord": coord})
    else:
        address = addresses[adID]['address']
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

async def cancel(update, context):
    #user = update.message.from_user
    #logger.info("User %s canceled the conversation." % user.first_name)
    await update.message.reply_text('Abgebrochen')

    return ConversationHandler.END