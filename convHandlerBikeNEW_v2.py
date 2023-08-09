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
        keyboard = []
        for ctr, address in enumerate(userData['addresses']['bike']):
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
    chatId = getChatId(update, context)
    userData = loadSingleUserData(chatId)
    if 'coord' in userData['addresses']['bike'][adID]:
        coord = userData['addresses']['bike'][adID]['coord']
        returnStr, fileName, errorCode = returnMinutely({"coord": coord})
    else:
        address = userData['addresses']['bike'][adID]['address']
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
    #user = update.message.from_user
    #logger.info("User %s canceled the conversation." % user.first_name)
    await update.message.reply_text('Abgebrochen')

    return ConversationHandler.END


def getConvHandlerBike():
    convHandlerBike = ConversationHandler(
        entry_points=[CommandHandler("fahrrad" ,bikeStart)],
        states={
            1: [CallbackQueryHandler(bikeEval)
                    ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerBike
