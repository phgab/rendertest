from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler
from weatherFuncts import returnMinutely


def bikeStart(update, context):

    keyboard = [[InlineKeyboardButton("Zuhause", callback_data="1")],
                [InlineKeyboardButton("MHH", callback_data="2")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Von wo möchtest du fahren? Zum Abbrechen \cancel.', reply_markup=reply_markup)

    return 1


def bikeEval(update, context):
    query = update.callback_query
    query.answer()
    bot = query.bot
    qData = query.data
    adID = int(qData)
    if adID == 1:
        address = 'Kriegerstrasse 22, 30161 Hannover'
    elif adID == 2:
        address = 'Stadtfelddamm 34, 30625 Hannover'

    returnStr, fileName, errorCode = returnMinutely({"address": address})

    if errorCode == -2:
        bot.sendMessage(query.message.chat.id, "Keine Adresse übermittelt")
    elif errorCode == -1:
        bot.sendMessage(query.message.chat.id, "Adresse konnte nicht gefunden werden")
    else:
        bot.send_photo(query.message.chat.id, open(fileName + ".jpg", 'rb'))
        bot.sendMessage(query.message.chat.id, returnStr)
    return ConversationHandler.END


def cancel(update, context):
    #user = update.message.from_user
    #logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Okay dann halt nicht -.-')

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
