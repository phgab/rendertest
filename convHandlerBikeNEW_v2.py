import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler
from weatherFuncts import returnMinutely
from actUserDataHandling import loadSingleUserData, getChatId


async def bikeStart(update, context):
    chatId = getChatId(update, context)
    userData = loadSingleUserData(chatId)
    if ('addresses' in userData and 'bike' in userData['addresses'] and
            0 < len(userData['addresses']['bike'])):
        addresses = userData['addresses']['bike']
        context.user_data['addresses'] = addresses
        keyboard = []
        numAdr = len(addresses)
        if 2 < numAdr:
            if (numAdr % 2) == 0:
                rng = range(int(numAdr / 2))
            else:
                rng = range(int((numAdr - 1) / 2))
            for idx in rng:
                keyboard.append([InlineKeyboardButton(addresses[idx * 2]['shortName'], callback_data=str(idx * 2)),
                                 InlineKeyboardButton(addresses[idx * 2 + 1]['shortName'],
                                                      callback_data=str(idx * 2 + 1))])
            if (numAdr % 2) == 1:
                keyboard.append(
                    [InlineKeyboardButton(addresses[numAdr - 1]['shortName'], callback_data=str(numAdr - 1))])
        else:
            for ctr, address in enumerate(userData['addresses']['weather']):
                keyboard.append([InlineKeyboardButton(address['shortName'], callback_data=str(ctr))])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Von wo möchtest du fahren? Zum Abbrechen \cancel.', reply_markup=reply_markup)
        return 1
    else:
        await update.message.reply_text('Es sind noch keine Fahrrad-Adressen gespeichert. ' +
                                        'Dies ist unter /einstellungen möglich.')
        return ConversationHandler.END


async def bikeEval(update, context):
    query = update.callback_query
    await query.answer()
    # bot = query.bot
    bot = context.bot
    qData = query.data
    adID = int(qData)
    addresses = context.user_data['addresses']
    if 'coord' in addresses[adID]:
        coord = addresses[adID]['coord']
        returnStr, fileName, errorCode = returnMinutely({"coord": coord})
    else:
        address = addresses[adID]['address']
        returnStr, fileName, errorCode = returnMinutely({"address": address})

    if errorCode == -2:
        await bot.sendMessage(query.message.chat.id, "Keine Adresse übermittelt")
    elif errorCode == -1:
        await bot.sendMessage(query.message.chat.id, "Adresse konnte nicht gefunden werden")
    else:
        await bot.send_photo(query.message.chat.id, open(fileName + ".jpg", 'rb'))
        await bot.sendMessage(query.message.chat.id, returnStr)
    return ConversationHandler.END


async def cancel(update, context):
    # user = update.message.from_user
    # logger.info("User %s canceled the conversation." % user.first_name)
    await update.message.reply_text('Abgebrochen')

    return ConversationHandler.END


def getConvHandlerBike():
    convHandlerBike = ConversationHandler(
        entry_points=[CommandHandler("fahrrad", bikeStart)],
        states={
            1: [CallbackQueryHandler(bikeEval)
                ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerBike
