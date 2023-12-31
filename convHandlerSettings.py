import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from actUserDataHandling import listUserAddresses, AUD_updateUserAddressData, getChatId
from weatherReader import findLatLon

FIRST, SECOND, THIRD = range(3)
L1, L2, L3, SELECT, ADD1, ADD2, ADD3, EDIT1, EDIT2, EDIT3, EDIT4, DEL1, DEL2 = range(13)
C1A, C1B, C2A, C2B, C2C, C3A, C3B, C3C, BACK = range(9)

# 1. a. Fahrradadressen bearbeiten, b. Wettervorherasge-Adressen bearbeiten (jeweils Kurzname und Adresse eintragen)
# 2. (jeweils): a. Adresse hinzufügen, b. Adressen bearbeiten, c. Adresse löschen
# Bei a. und b. jeweils Feedback über die ermittelte Adresse

def getConvHandlerSettings():
    convHandlerSettings = ConversationHandler(
        entry_points=[CommandHandler("einstellungen", settingsFirstLayer)],
        states={
            L1: [CallbackQueryHandler(settingsFirstLayer)],
            L2: [CallbackQueryHandler(settingsSecondLayer_bike, pattern='^' + str(C1A) + '$'),
                 CallbackQueryHandler(settingsSecondLayer_weather, pattern='^' + str(C1B) + '$')],
            L3: [CallbackQueryHandler(addAddress, pattern='^' + str(C2A) + '$'),
                 CallbackQueryHandler(selectAddressModify, pattern='^' + str(C2B) + '$'),
                 CallbackQueryHandler(selectAddressDelete, pattern='^' + str(C2C) + '$')],
            ADD1: [MessageHandler(filters.TEXT & (~ filters.COMMAND), addShortName)],
            ADD2: [MessageHandler(filters.TEXT & (~ filters.COMMAND), confirmAddition)],
            ADD3: [CallbackQueryHandler(saveNewAddress, pattern='^' + str(C3A) + '$'),
                   CallbackQueryHandler(addAddress, pattern='^' + str(C3B) + '$'),
                   CallbackQueryHandler(cancel, pattern='^' + str(C3C) + '$')],
            EDIT1: [CallbackQueryHandler(modifyAddress)],
            EDIT2: [MessageHandler(filters.TEXT & (~ filters.COMMAND), modifyShortName)],
            EDIT3: [MessageHandler(filters.TEXT & (~ filters.COMMAND), confirmModification)],
            EDIT4: [CallbackQueryHandler(saveModifiedAddress, pattern='^' + str(C3A) + '$'),
                    CallbackQueryHandler(modifyAddress, pattern='^' + str(C3B) + '$'), #todo:straighten out
                    CallbackQueryHandler(cancel, pattern='^' + str(C3C) + '$')],
            DEL1: [CallbackQueryHandler(confirmDeletion)],
            DEL2: [CallbackQueryHandler(deleteAddress, pattern='^' + str(C3A) + '$'),
                   CallbackQueryHandler(cancel, pattern='^' + str(C3B) + '$')]
            },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    return convHandlerSettings

async def settingsFirstLayer(update, context):
    keyboard = [[InlineKeyboardButton("Fahrrad-Adressen bearbeiten", callback_data=str(C1A))],
                [InlineKeyboardButton("Wettervorhersage-Adressen bearbeiten", callback_data=str(C1B))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
    return L2

def getSecondLayerKeyboard():
    keyboard = [[InlineKeyboardButton("Adresse hinzufügen", callback_data=str(C2A))],
                [InlineKeyboardButton("Adressen bearbeiten", callback_data=str(C2B))],
                [InlineKeyboardButton("Adresse löschen", callback_data=str(C2C))]]
    return keyboard

async def settingsSecondLayer_bike(update, context):
    context.user_data['L1'] = 'bike'
    chatId = getChatId(update, context)
    addressData_all = listUserAddresses(chatId)
    if 'bike' in addressData_all:
        addressData = addressData_all['bike']
    else:
        addressData = []
    context.user_data['addresses'] = addressData

    query = update.callback_query
    await query.answer()
    keyboard = getSecondLayerKeyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Aktion für Fahrrad-Adressen wählen:', reply_markup=reply_markup)
    return L3

async def settingsSecondLayer_weather(update, context):
    context.user_data['L1'] = 'weather'
    chatId = getChatId(update, context)
    addressData_all = listUserAddresses(chatId)
    if 'weather' in addressData_all:
        addressData = addressData_all['weather']
    else:
        addressData = []
    context.user_data['addresses'] = addressData

    query = update.callback_query
    await query.answer()
    keyboard = getSecondLayerKeyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text('Aktion für Wettervorhersage-Adressen wählen:', reply_markup=reply_markup)
    return L3


async def addAddress(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Bitte die Adresse inkl. PLZ und Ort senden.")
    return ADD1

async def addShortName(update, context):
    address = update.message.text
    context.user_data['newAddress'] = address
    await update.message.reply_text(text="Bitte eine Kurzbeschreibung für die Adresse " + address + " senden.")
    return ADD2

async def confirmAddition(update, context):
    shortName = update.message.text
    context.user_data['newShortName'] = shortName
    address = context.user_data['newAddress']
    coord = findLatLon(address)
    context.user_data['newCoord'] = coord

    keyboard = [[InlineKeyboardButton("Ja", callback_data=str(C3A))],
                [InlineKeyboardButton("Neu eingeben", callback_data=str(C3B))],
                [InlineKeyboardButton("Abbrechen", callback_data=str(C3C))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    replyText = ('Addresse gefunden in ' + coord['place'] + '.\n' +
                 'Soll die Addresse "' + address + ' (' + shortName + ')" gespeichert werden?')
    await update.message.reply_text(replyText, reply_markup=reply_markup)
    return ADD3

async def saveNewAddress(update, context):
    globalDB_var = context.bot_data['globalDB_var']
    chatId = getChatId(update, context)
    addressType = context.user_data['L1']
    oldAddressData = context.user_data['addresses']
    address = context.user_data['newAddress']
    shortName = context.user_data['newShortName']
    coord = context.user_data['newCoord']

    newAddressData = oldAddressData
    newAddressData.append({'address': address, 'shortName': shortName, 'coord': coord})
    await AUD_updateUserAddressData(globalDB_var, chatId, addressType, newAddressData)

    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Hinzufügen erfolgreich.")

    return ConversationHandler.END

def getSelectionKeyboard(update, context):
    addressData = context.user_data['addresses']
    keyboard = []
    for ctr, address in enumerate(addressData):
        buttonText = '"' + address['shortName'] + '": ' + address['address']
        buttonCallback = 'Field_' + str(ctr)
        keyboard.append([InlineKeyboardButton(buttonText, callback_data=buttonCallback)])
    return keyboard

async def selectAddressModify(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = getSelectionKeyboard(update, context)
    if len(keyboard) == 0:
        await query.edit_message_text(text="Hier sind noch keine Adressen eingetragen. Vorgang wird abgebrochen.")
        return ConversationHandler.END
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Adresse zum Bearbeiten wählen:', reply_markup=reply_markup)
        return EDIT1

async def modifyAddress(update, context):
    query = update.callback_query
    qData = query.data
    if 'Field_' in qData:
        # if not: rerun from previous try
        chosenIdx = int(qData.replace('Field_', ''))
        context.user_data['chosenIdx'] = chosenIdx
        chosenAddress = context.user_data['addresses'][chosenIdx]
        context.user_data['oldAddress'] = chosenAddress['address']
        context.user_data['oldShortName'] = chosenAddress['shortName']
        context.user_data['oldCoord'] = chosenAddress['coord']
    replyText = ('Gespeicherte Adresse:\n' + context.user_data['oldAddress'] + '\n' +
                 'Bitte die aktualisierte Adresse inkl. PLZ und Ort senden.')
    await query.answer()
    # switch_inline_query_current_chat ?
    await query.edit_message_text(text=replyText)
    return EDIT2

async def modifyShortName(update, context):
    address = update.message.text
    context.user_data['newAddress'] = address
    replyText = ('Gespeicherte Kurzbeschreibung:\n' + context.user_data['oldShortName'] + '\n' +
                 'Bitte die aktualisierte Kurzbeschreibung senden.')
    await update.message.reply_text(text=replyText)
    return EDIT3

async def confirmModification(update, context):
    shortName = update.message.text
    context.user_data['newShortName'] = shortName
    address = context.user_data['newAddress']
    oldShortName = context.user_data['oldShortName']
    oldAddress = context.user_data['oldAddress']
    coord = findLatLon(address)
    context.user_data['newCoord'] = coord

    keyboard = [[InlineKeyboardButton("Ja", callback_data=str(C3A))],
                [InlineKeyboardButton("Neu eingeben", callback_data=str(C3B))],
                [InlineKeyboardButton("Abbrechen", callback_data=str(C3C))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    replyText = ('Adresse gefunden in ' + coord['place'] + '.\n' +
                 'Soll die Adresse \n"' + oldAddress + ' (' + oldShortName + ')" zu \n'
                 + address + ' (' + shortName + ')" \ngeändert werden?')
    await update.message.reply_text(replyText, reply_markup=reply_markup)
    return EDIT4

async def saveModifiedAddress(update, context):
    globalDB_var = context.bot_data['globalDB_var']
    chatId = getChatId(update, context)
    chosenIdx = context.user_data['chosenIdx']
    addressType = context.user_data['L1']
    oldAddressData = context.user_data['addresses']
    address = context.user_data['newAddress']
    shortName = context.user_data['newShortName']
    coord = context.user_data['newCoord']

    newAddressData = oldAddressData
    newAddressData[chosenIdx] = {'address': address, 'shortName': shortName, 'coord': coord}
    await AUD_updateUserAddressData(globalDB_var, chatId, addressType, newAddressData)

    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Bearbeitung erfolgreich.")

    return ConversationHandler.END

async def selectAddressDelete(update, context):
    query = update.callback_query
    await query.answer()

    keyboard = getSelectionKeyboard(update, context)
    if len(keyboard) == 0:
        await query.edit_message_text(text="Hier sind noch keine Adressen eingetragen. Vorgang wird abgebrochen.")
        return ConversationHandler.END
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Adresse zum Löschen wählen:', reply_markup=reply_markup)
        return DEL1

async def confirmDeletion(update, context):
    query = update.callback_query
    qData = query.data
    chosenIdx = int(qData.replace('Field_', ''))
    context.user_data['chosenField'] = chosenIdx
    chosenAddress = context.user_data['addresses'][chosenIdx]
    oldAddress = chosenAddress['address']
    oldShortName = chosenAddress['shortName']
    replyText = ('Soll die Adresse \n"' + oldAddress + ' (' +
                 oldShortName + ')"\n wirklich gelöscht werden?')

    keyboard = [[InlineKeyboardButton("Ja", callback_data=str(C3A))],
                [InlineKeyboardButton("Nein", callback_data=str(C3B))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(replyText, reply_markup=reply_markup)

    return DEL2

async def deleteAddress(update, context):
    globalDB_var = context.bot_data['globalDB_var']
    chatId = getChatId(update, context)
    addressType = context.user_data['L1']

    chosenIdx = context.user_data['chosenField']
    oldAddressData = context.user_data['addresses']
    newAddressData = oldAddressData
    del newAddressData[chosenIdx]
    await AUD_updateUserAddressData(globalDB_var, chatId, addressType, newAddressData)

    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Löschung erfolgreich.")

    return ConversationHandler.END

async def cancel(update, context):
    # user = update.message.from_user
    #logger.info("User %s canceled the conversation." % user.first_name)
    await update.message.reply_text('Abgebrochen')

    return ConversationHandler.END
