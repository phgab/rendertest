import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from actUserDataHandling import loadSingleUserData, AUD_updateUserAddressData, getChatId, AUD_addUserCronJobData, AUD_updateUserCronJobData, AUD_deleteUserCronJobData
from weatherReader import findLatLon

(SELECT, DETAILS, TOGGLE, DELETE,
 TYPE, SCH_WDAYS, SCH_HOURS, SCH_MIN,
 TITLE, CONFIRM, SAVE, ERROR) = range(12)
(L1_NEW, L1_SHOW, L1_EDIT, L1_TOGGLE, L1_DELETE,
 CNFRM_EDIT, CNFRM_DEL, ABORT, BACK, MANUAL_SEL,
 TYPE_BIKE, TYPE_WEATHER,
 WD_WEEK, WD_WE, WD_ALL,
 MIN_0, MIN_15, MIN_30, MIN_45,
 ERR_INPUT
 ) = range(20)


# 1. a. Erinnerung hinzufügen, b. Meine Erinnerungen anzeigen, c. Erinnerungen bearbeiten, d. Erinnerungen aktivieren/deaktivieren, e. Erinnerung löschen
# a.: Iteration durch alle notwendigen Felder
#     TD: Implementierung als conv handler
# b-e.: jeweils 1 Button mit Titel
#      TD: Implementierung als dieselbe Funktion, Überfunktion wird in context gespeichert
# b.: bei Klick werden Details angezeigt
# c.: Bei Klick Buttons mit den jeweiligen bearbeitbaren / zu erstellenden Feldern
# e.: are you sure?
# todo: vllt durch context vars integrieren, dass auch einzelne Felder bearbeitet werden können, mit
# a. ['editSingle'] und b. ['editEntered'] um die jeweils zweite Funktion dann wieder zu verlassen


def getConvHandlerCron():
    convHandlerCron = ConversationHandler(
        entry_points=[CommandHandler("erinnerungen", cronFirstLayer)],
        states={
            SELECT: [CallbackQueryHandler(selectJob, pattern='^(?!.*' + L1_NEW + ').*$'),  # everything except
                     CallbackQueryHandler(startNewJob, pattern='^' + str(L1_NEW) + '$')],
            DETAILS: [CallbackQueryHandler(showJobDetails)],
            TOGGLE: [CallbackQueryHandler(toggleJob)],
            DELETE: [CallbackQueryHandler(deleteJob)],
            # new/edit steps
            TYPE: [CallbackQueryHandler(selectJobType)],
            SCH_WDAYS: [CallbackQueryHandler(selectWDays)],
            SCH_HOURS: [CallbackQueryHandler(enterHours, pattern='^(?!.*' + MANUAL_SEL + ').*$'),
                        CallbackQueryHandler(enterWDays, pattern='^' + str(MANUAL_SEL) + '$'),
                        MessageHandler(filters.TEXT, readWDays_enterHours)],
            SCH_MIN: [MessageHandler(filters.TEXT, readHours_selectMin)],
            TITLE: [CallbackQueryHandler(enterTitle, pattern='^(?!.*' + MANUAL_SEL + ').*$'),
                    CallbackQueryHandler(enterMin, pattern='^' + str(MANUAL_SEL) + '$'),
                    MessageHandler(filters.TEXT, readMin_enterTitle)],
            CONFIRM: [MessageHandler(filters.TEXT, confirmJob)],
            SAVE: [CallbackQueryHandler(saveEdit, pattern='^' + str(CNFRM_EDIT) + '$'),
                   CallbackQueryHandler(saveDeletion, pattern='^' + str(CNFRM_DEL) + '$'),
                   CallbackQueryHandler(cancel, pattern='^' + str(ABORT) + '$')],
            ERROR: [CallbackQueryHandler(error_input, pattern='^' + str(ERR_INPUT) + '$')]
            },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerCron

async def cronFirstLayer(update, context):
    if 'chatId' not in context.user_data:
        chatId = getChatId(update, context)
        context.user_data['chatId'] = chatId
        context.user_data['cronJobs'] = listUserCronJobs(chatId)
    keyboard = [[InlineKeyboardButton("Erinnerung hinzufügen", callback_data=str(L1_NEW))],
                [InlineKeyboardButton("Meine Erinnerungen anzeigen", callback_data=str(L1_SHOW))],
                [InlineKeyboardButton("Erinnerungen bearbeiten", callback_data=str(L1_EDIT))],
                [InlineKeyboardButton("Erinnerungen aktivieren/deaktivieren", callback_data=str(L1_TOGGLE))],
                [InlineKeyboardButton("Erinnerung löschen", callback_data=str(L1_DELETE))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
    return SELECT

def listUserCronJobs(chatId):
    userData = loadSingleUserData(chatId)
    if 'cronJobs' in userData:
        cronJobs = userData['cronJobs']
    else:
        cronJobs = []
    return cronJobs

async def selectJob(update, context):
    query = update.callback_query
    qData = query.data
    returndict = {str(L1_SHOW): DETAILS, str(L1_EDIT): TYPE, str(L1_TOGGLE): TOGGLE, str(L1_DELETE): DELETE}
    if qData == str(L1_EDIT):
        context.user_data['editType'] = 'edit'
    cronJobs = context.user_data['cronJobs']
    keyboard = []
    for idxJ, jobData in enumerate(cronJobs):
        jobNum = str(idxJ + 1)
        jobTitle = jobData['title']
        # jobSchedule = jobData['cronData']['job']['schedule']
        nameStr = jobNum + ': ' + jobTitle
        keyboard.append([InlineKeyboardButton(nameStr, callback_data=str(idxJ))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Aktion für Fahrrad-Adressen wählen:', reply_markup=reply_markup)
    return returndict[qData]

async def startNewJob(update, context):
    query = update.callback_query
    context.user_data['editType'] = 'new'
    # DOES THIS WORK?
    await selectJobType(update, context)


async def showJobDetails(update, context):
    query = update.callback_query
    qData = query.data
    jobNum = int(qData)
    cronJobs = context.user_data['cronJobs']
    cronJob = cronJobs[jobNum]
    jobNumStr = str(jobNum + 1)
    jobTitle = cronJob['title']
    jobSchedule = cronJob['cronData']['job']['schedule']
    scheduleStr = scheduleDict2Str(jobSchedule)
    await query.edit_message_text('Aktion für Fahrrad-Adressen wählen:')


def scheduleDict2Str(scheduleDict):
    scheduleStr = 'schedule'
    return scheduleStr

async def toggleJob(update, context):
    query = update.callback_query
    qData = query.data

async def deleteJob(update, context):
    query = update.callback_query
    qData = query.data

async def saveDeletion(update, context):
    query = update.callback_query
    qData = query.data

async def selectJobType(update, context):
    query = update.callback_query
    qData = query.data

async def selectWDays(update, context):
    query = update.callback_query
    qData = query.data

async def enterWDays(update, context):
    t=0

async def readWDays_enterHours(update, context):
    wDaysMsg = update.message.text

async def enterHours(update, context):
    query = update.callback_query
    qData = query.data

async def readHours_selectMin(update, context):
    hrsMsg = update.message.text

async def enterTitle(update, context):
    query = update.callback_query
    qData = query.data

async def enterMin(update, context):
    query = update.callback_query
    qData = query.data

async def readMin_enterTitle(update, context):
    minMsg = update.message.text

async def confirmJob(update, context):
    title = update.message.text

async def saveEdit(update, context):
    t=0

async def error_input(update, context):
    query = update.callback_query
    qData = query.data

async def cancel(update, context):
    # user = update.message.from_user
    #logger.info("User %s canceled the conversation." % user.first_name)
    await update.message.reply_text('Abgebrochen')

    return ConversationHandler.END


# def getSecondLayerKeyboard():
#     keyboard = [[InlineKeyboardButton("Adresse hinzufügen", callback_data=str(C2A))],
#                 [InlineKeyboardButton("Adressen bearbeiten", callback_data=str(C2B))],
#                 [InlineKeyboardButton("Adresse löschen", callback_data=str(C2C))]]
#     return keyboard
#
# # todo: kill this
# def listUserAddresses(chatId):
#     return []
#
# async def settingsSecondLayer_bike(update, context):
#     context.user_data['L1'] = 'bike'
#     chatId = getChatId(update, context)
#     addressData_all = listUserAddresses(chatId)
#     if 'bike' in addressData_all:
#         addressData = addressData_all['bike']
#     else:
#         addressData = []
#     context.user_data['addresses'] = addressData
#
#     query = update.callback_query
#     await query.answer()
#     keyboard = getSecondLayerKeyboard()
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text('Aktion für Fahrrad-Adressen wählen:', reply_markup=reply_markup)
#     return L3
#
# async def settingsSecondLayer_weather(update, context):
#     context.user_data['L1'] = 'weather'
#     chatId = getChatId(update, context)
#     addressData_all = listUserAddresses(chatId)
#     if 'weather' in addressData_all:
#         addressData = addressData_all['weather']
#     else:
#         addressData = []
#     context.user_data['addresses'] = addressData
#
#     query = update.callback_query
#     await query.answer()
#     keyboard = getSecondLayerKeyboard()
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text('Aktion für Wettervorhersage-Adressen wählen:', reply_markup=reply_markup)
#     return L3
#
#
#
#
# async def addAddress(update, context):
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text(text="Bitte die Adresse inkl. PLZ und Ort senden.")
#     return ADD1
#
# async def addShortName(update, context):
#     address = update.message.text
#     context.user_data['newAddress'] = address
#     await update.message.reply_text(text="Bitte eine Kurzbeschreibung für die Adresse " + address + " senden.")
#     return ADD2
#
# async def confirmAddition(update, context):
#     shortName = update.message.text
#     context.user_data['newShortName'] = shortName
#     address = context.user_data['newAddress']
#     coord = findLatLon(address)
#     context.user_data['newCoord'] = coord
#
#     keyboard = [[InlineKeyboardButton("Ja", callback_data=str(C3A))],
#                 [InlineKeyboardButton("Neu eingeben", callback_data=str(C3B))],
#                 [InlineKeyboardButton("Abbrechen", callback_data=str(C3C))]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     replyText = ('Addresse gefunden in ' + coord['place'] + '.\n' +
#                  'Soll die Addresse "' + address + ' (' + shortName + ')" gespeichert werden?')
#     await update.message.reply_text(replyText, reply_markup=reply_markup)
#     return ADD3
#
# async def saveNewAddress(update, context):
#     globalDB_var = context.bot_data['globalDB_var']
#     chatId = getChatId(update, context)
#     addressType = context.user_data['L1']
#     oldAddressData = context.user_data['addresses']
#     address = context.user_data['newAddress']
#     shortName = context.user_data['newShortName']
#     coord = context.user_data['newCoord']
#
#     newAddressData = oldAddressData
#     newAddressData.append({'address': address, 'shortName': shortName, 'coord': coord})
#     AUD_updateUserAddressData(globalDB_var, chatId, addressType, newAddressData)
#
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text(text="Hinzufügen erfolgreich.")
#
#     return ConversationHandler.END
#
# def getSelectionKeyboard(update, context):
#     addressData = context.user_data['addresses']
#     keyboard = []
#     for ctr, address in enumerate(addressData):
#         buttonText = '"' + address['shortName'] + '": ' + address['address']
#         buttonCallback = 'Field_' + str(ctr)
#         keyboard.append([InlineKeyboardButton(buttonText, callback_data=buttonCallback)])
#     return keyboard
#
# async def selectAddressModify(update, context):
#     query = update.callback_query
#     await query.answer()
#
#     keyboard = getSelectionKeyboard(update, context)
#     if len(keyboard) == 0:
#         await query.edit_message_text(text="Hier sind noch keine Adressen eingetragen. Vorgang wird abgebrochen.")
#         return ConversationHandler.END
#     else:
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await query.edit_message_text('Adresse zum Bearbeiten wählen:', reply_markup=reply_markup)
#         return EDIT1
#
# async def modifyAddress(update, context):
#     query = update.callback_query
#     qData = query.data
#     if 'Field_' in qData:
#         # if not: rerun from previous try
#         chosenIdx = int(qData.replace('Field_', ''))
#         context.user_data['chosenIdx'] = chosenIdx
#         chosenAddress = context.user_data['addresses'][chosenIdx]
#         context.user_data['oldAddress'] = chosenAddress['address']
#         context.user_data['oldShortName'] = chosenAddress['shortName']
#         context.user_data['oldCoord'] = chosenAddress['coord']
#     replyText = ('Gespeicherte Adresse:\n' + context.user_data['oldAddress'] + '\n' +
#                  'Bitte die aktualisierte Adresse inkl. PLZ und Ort senden.')
#     await query.answer()
#     # switch_inline_query_current_chat ?
#     await query.edit_message_text(text=replyText)
#     return EDIT2
#
# async def modifyShortName(update, context):
#     address = update.message.text
#     context.user_data['newAddress'] = address
#     replyText = ('Gespeicherte Kurzbeschreibung:\n' + context.user_data['oldShortName'] + '\n' +
#                  'Bitte die aktualisierte Kurzbeschreibung senden.')
#     await update.message.reply_text(text=replyText)
#     return EDIT3
#
# async def confirmModification(update, context):
#     shortName = update.message.text
#     context.user_data['newShortName'] = shortName
#     address = context.user_data['newAddress']
#     oldShortName = context.user_data['oldShortName']
#     oldAddress = context.user_data['oldAddress']
#     coord = findLatLon(address)
#     context.user_data['newCoord'] = coord
#
#     keyboard = [[InlineKeyboardButton("Ja", callback_data=str(C3A))],
#                 [InlineKeyboardButton("Neu eingeben", callback_data=str(C3B))],
#                 [InlineKeyboardButton("Abbrechen", callback_data=str(C3C))]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     replyText = ('Adresse gefunden in ' + coord['place'] + '.\n' +
#                  'Soll die Adresse \n"' + oldAddress + ' (' + oldShortName + ')" zu \n'
#                  + address + ' (' + shortName + ')" \ngeändert werden?')
#     await update.message.reply_text(replyText, reply_markup=reply_markup)
#     return EDIT4
#
# async def saveModifiedAddress(update, context):
#     globalDB_var = context.bot_data['globalDB_var']
#     chatId = getChatId(update, context)
#     chosenIdx = context.user_data['chosenIdx']
#     addressType = context.user_data['L1']
#     oldAddressData = context.user_data['addresses']
#     address = context.user_data['newAddress']
#     shortName = context.user_data['newShortName']
#     coord = context.user_data['newCoord']
#
#     newAddressData = oldAddressData
#     newAddressData[chosenIdx] = {'address': address, 'shortName': shortName, 'coord': coord}
#     AUD_updateUserAddressData(globalDB_var, chatId, addressType, newAddressData)
#
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text(text="Bearbeitung erfolgreich.")
#
#     return ConversationHandler.END
#
# async def selectAddressDelete(update, context):
#     query = update.callback_query
#     await query.answer()
#
#     keyboard = getSelectionKeyboard(update, context)
#     if len(keyboard) == 0:
#         await query.edit_message_text(text="Hier sind noch keine Adressen eingetragen. Vorgang wird abgebrochen.")
#         return ConversationHandler.END
#     else:
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await query.edit_message_text('Adresse zum Löschen wählen:', reply_markup=reply_markup)
#         return DEL1
#
# async def confirmDeletion(update, context):
#     query = update.callback_query
#     qData = query.data
#     chosenIdx = int(qData.replace('Field_', ''))
#     context.user_data['chosenField'] = chosenIdx
#     chosenAddress = context.user_data['addresses'][chosenIdx]
#     oldAddress = chosenAddress['address']
#     oldShortName = chosenAddress['shortName']
#     replyText = ('Soll die Adresse \n"' + oldAddress + ' (' +
#                  oldShortName + ')"\n wirklich gelöscht werden?')
#
#     keyboard = [[InlineKeyboardButton("Ja", callback_data=str(C3A))],
#                 [InlineKeyboardButton("Nein", callback_data=str(C3B))]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     await query.answer()
#     await query.edit_message_text(replyText, reply_markup=reply_markup)
#
#     return DEL2
#
# async def deleteAddress(update, context):
#     globalDB_var = context.bot_data['globalDB_var']
#     chatId = getChatId(update, context)
#     addressType = context.user_data['L1']
#
#     chosenIdx = context.user_data['chosenField']
#     oldAddressData = context.user_data['addresses']
#     newAddressData = oldAddressData
#     del newAddressData[chosenIdx]
#     AUD_updateUserAddressData(globalDB_var, chatId, addressType, newAddressData)
#
#     query = update.callback_query
#     await query.answer()
#     await query.edit_message_text(text="Löschung erfolgreich.")
#
#     return ConversationHandler.END
#
#
