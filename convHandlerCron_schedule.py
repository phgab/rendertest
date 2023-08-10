import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from actUserDataHandling import loadSingleUserData, AUD_updateUserAddressData, getChatId, AUD_addUserCronJobData, AUD_updateUserCronJobData, AUD_deleteUserCronJobData
from weatherReader import findLatLon

FIRST, SECOND, THIRD = range(3)
L1, L2, L3, SELECT, ADD1, ADD2, ADD3, EDIT1, EDIT2, EDIT3, EDIT4, DEL1, DEL2 = range(13)
C1A, C1B, C1C, C1D, C1E, C2A, C2B, C2C, C3A, C3B, C3C, BACK = range(12)

def getConvHandlerCronSchedule():
    convHandlerCronSchedule = ConversationHandler(
        entry_points=[CallbackQueryHandler(startNewSchedule, pattern='^' + str(SCH_NEW) + '$'),
                      CallbackQueryHandler(startEditSchedule, pattern='^' + str(SCH_EDIT) + '$')],
        states={
            L1: [CallbackQueryHandler(cronFirstLayer)],
            L2: [CallbackQueryHandler(settingsSecondLayer_bike, pattern='^' + str(C1A) + '$'),
                 CallbackQueryHandler(settingsSecondLayer_weather, pattern='^' + str(C1B) + '$')],
            L3: [CallbackQueryHandler(addAddress, pattern='^' + str(C2A) + '$'),
                 CallbackQueryHandler(selectAddressModify, pattern='^' + str(C2B) + '$'),
                 CallbackQueryHandler(selectAddressDelete, pattern='^' + str(C2C) + '$')],
            ADD1: [MessageHandler(filters.TEXT, addShortName)],
            ADD2: [MessageHandler(filters.TEXT, confirmAddition)],
            ADD3: [CallbackQueryHandler(saveNewAddress, pattern='^' + str(C3A) + '$'),
                   CallbackQueryHandler(addAddress, pattern='^' + str(C3B) + '$'),
                   CallbackQueryHandler(cancel, pattern='^' + str(C3C) + '$')],
            EDIT1: [CallbackQueryHandler(modifyAddress)],
            EDIT2: [MessageHandler(filters.TEXT, modifyShortName)],
            EDIT3: [MessageHandler(filters.TEXT, confirmModification)],
            EDIT4: [CallbackQueryHandler(saveModifiedAddress, pattern='^' + str(C3A) + '$'),
                    CallbackQueryHandler(modifyAddress, pattern='^' + str(C3B) + '$'), #todo:straighten out
                    CallbackQueryHandler(cancel, pattern='^' + str(C3C) + '$')],
            DEL1: [CallbackQueryHandler(confirmDeletion)],
            DEL2: [CallbackQueryHandler(deleteAddress, pattern='^' + str(C3A) + '$'),
                   CallbackQueryHandler(cancel, pattern='^' + str(C3B) + '$')]
            },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerCron