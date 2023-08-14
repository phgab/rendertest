import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from actUserDataHandling import listUserAddresses, listUserCronJobs, AUD_updateUserAddressData, getChatId, AUD_addUserCronJobData, AUD_updateUserCronJobData, AUD_deleteUserCronJobData
from weatherReader import findLatLon
from emoji import emojize

(SELECT, DETAILS, TOGGLE, DELETE,
 TYPE, ADDRESS, SCH_WDAYS, SCH_HOURS, SCH_MIN,
 TITLE, CONFIRM, SAVE, ERROR) = range(13)
(L1_NEW, L1_SHOW, L1_EDIT, L1_TOGGLE, L1_DELETE,
 CNFRM_EDIT, CNFRM_DEL, ABORT, BACK, LIST_SEL, MANUAL_SEL,
 TYPE_BIKE, TYPE_WEATHER,
 WD_WEEK, WD_WE, WD_ALL,
 MIN_0, MIN_15, MIN_30, MIN_45,
 ERR_INPUT
 ) = range(21)


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
                     CallbackQueryHandler(selectJobType, pattern='^' + str(L1_NEW) + '$')],
            DETAILS: [CallbackQueryHandler(showJobDetails)],
            TOGGLE: [CallbackQueryHandler(toggleJob)],
            DELETE: [CallbackQueryHandler(deleteJob)],
            # new/edit steps
            TYPE: [CallbackQueryHandler(selectJobType)],
            ADDRESS: [CallbackQueryHandler(selectAddressMethod, pattern=('^' + str(TYPE_BIKE) + '|' +
                                                                            str(TYPE_WEATHER) + '$')),
                         CallbackQueryHandler(selectAddress, pattern='^' + str(LIST_SEL) + '$'),
                         CallbackQueryHandler(enterAddress, pattern='^' + str(MANUAL_SEL) + '$')],
            SCH_WDAYS: [CallbackQueryHandler(selectWDays),
                        MessageHandler(filters.TEXT, readAddress_selectWDays)],
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
        context.user_data['addresses'] = listUserAddresses(chatId)
    keyboard = [[InlineKeyboardButton("Erinnerung hinzufügen", callback_data=str(L1_NEW))],
                [InlineKeyboardButton("Meine Erinnerungen anzeigen", callback_data=str(L1_SHOW))],
                [InlineKeyboardButton("Erinnerungen bearbeiten", callback_data=str(L1_EDIT))],
                [InlineKeyboardButton("Erinnerungen aktivieren / deaktivieren", callback_data=str(L1_TOGGLE))],
                [InlineKeyboardButton("Erinnerung löschen", callback_data=str(L1_DELETE))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bitte wählen:', reply_markup=reply_markup)
    return SELECT


async def selectJob(update, context):
    query = update.callback_query
    qData = query.data
    returnDict = {str(L1_SHOW): DETAILS,
                  str(L1_EDIT): TYPE,
                  str(L1_TOGGLE): TOGGLE,
                  str(L1_DELETE): DELETE}
    msgDict = {str(L1_SHOW): 'zur detaillierten Ansicht',
               str(L1_EDIT): 'zum Bearbeiten',
               str(L1_TOGGLE): 'zum Aktivieren / Deaktivieren',
               str(L1_DELETE): 'zum Löschen'}
    if qData == str(L1_EDIT):
        context.user_data['editType'] = 'edit'
    cronJobs = context.user_data['cronJobs']
    keyboard = []
    if len(cronJobs) == 0:
        await query.edit_message_text('Hier sind noch keine Daten vorhanden.')
        return ConversationHandler.END
    else:
        for idxJ, jobData in enumerate(cronJobs):
            jobNum = str(idxJ + 1)
            jobTitle = jobData['title']
            jobActivation = jobData['cronData']['job']['enabled']
            if not jobActivation:
                nameStr = emojize(":prohibited: ", use_aliases=True) + jobNum + ': ' + jobTitle
            else:
                nameStr = jobNum + ': ' + jobTitle
            keyboard.append([InlineKeyboardButton(nameStr, callback_data=str(idxJ))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Erinnerung ' + msgDict[qData] + ' auswählen:',
                                      reply_markup=reply_markup)
        return returnDict[qData]


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
    detailStr = ('Ausgewählte Erinnerung: \n' +
                 '#' + jobNumStr + ': "' + jobTitle + '"\n' +
                 scheduleStr)
    await query.edit_message_text(detailStr)
    return ConversationHandler.END


def scheduleDict2Str(scheduleDict):
    wdays = sorted(scheduleDict['wdays'])
    hours = sorted(scheduleDict['hours'])
    minutes = sorted(scheduleDict['minutes'])
    if 0 < len(wdays):
        if wdays == list(range(7)):
            wDaysStr = 'Täglich'
        elif sorted(wdays) == list(range(1, 6)):
            wDaysStr = 'An Wochentagen'
        elif sorted(wdays) == [5, 6]:
            wDaysStr = 'An Wochenendstagen'
        else:
            wDaysList = ['Sonntags', 'Montags', 'Dienstags', 'Mittwochs',
                         'Donnerstags', 'Freitags', 'Samstags']
            numWDays = len(wdays)
            wdays_temp = sorted([(day - 1) % 7 for day in wdays])
            wdays_sun = [(day + 1) % 7 for day in wdays_temp]

            wDaysStr = wDaysList[wdays_sun[0]]
            for idx in range(1, numWDays - 1):
                wDaysStr = wDaysStr + ', ' + wDaysList[wdays_sun[idx]]
            if 1 < numWDays:
                wDaysStr = wDaysStr + ' und ' + wDaysList[wdays_sun[numWDays - 1]]
    else:
        wDaysStr = ''
    numHours = len(hours)
    numMinutes = len(minutes)
    if 0 < numHours * numMinutes:
        timeStr = str(hours[0]).zfill(2) + ':' + str(minutes[0]).zfill(2)
        for idxH in range(numHours):
            for idxM in range(numMinutes):
                if (idxH + 1) * (idxM + 1) == 1:
                    continue
                elif (idxH + 1) * (idxM + 1) == numHours * numMinutes:
                    timeStr = (timeStr + ' und ' +
                               str(hours[idxH]).zfill(2) + ':' + str(minutes[idxM]).zfill(2))
                else:
                    timeStr = (timeStr + ', ' +
                               str(hours[idxH]).zfill(2) + ':' + str(minutes[idxM]).zfill(2))
        if 0 < len(wdays):
            scheduleStr = wDaysStr + ' um ' + timeStr
        else:
            scheduleStr = timeStr
    elif 0 < numHours:
        timeStr = str(hours[0]).zfill(2)
        for idxH in range(numHours):
            if (idxH + 1) == 1:
                continue
            elif (idxH + 1) == numHours:
                timeStr = timeStr + ' und ' + str(hours[idxH]).zfill(2)
            else:
                timeStr = timeStr + ', ' + str(hours[idxH]).zfill(2)
        if 0 < len(wdays):
            scheduleStr = wDaysStr + ' zu den Stunden ' + timeStr
        else:
            scheduleStr = timeStr
    elif 0 < numMinutes:
        timeStr = str(minutes[0]).zfill(2)
        for idxM in range(numMinutes):
            if (idxM + 1) == 1:
                continue
            elif (idxM + 1) == numMinutes:
                timeStr = timeStr + ' und ' + str(minutes[idxM]).zfill(2)
            else:
                timeStr = timeStr + ', ' + str(minutes[idxM]).zfill(2)
        if 0 < len(wdays):
            scheduleStr = wDaysStr + ' zu den Minuten ' + timeStr
        else:
            scheduleStr = timeStr
    else:
        scheduleStr = wDaysStr

    return scheduleStr


async def toggleJob(update, context):
    query = update.callback_query
    qData = query.data
    globalDB_var = context.bot_data['globalDB_var']
    chatId = context.user_data['chatId']
    jobNum = int(qData)
    jobTitle = context.user_data['cronJobs'][jobNum]['title']
    enabled = context.user_data['cronJobs'][jobNum]['cronData']['job']['enabled']

    cronJobs = await AUD_updateUserCronJobData(globalDB_var, chatId, jobNum, enabled=not enabled)
    context.user_data['cronJobs'] = cronJobs
    toggleStr = 'Erinnerung #' + str(jobNum) + ': ' + jobTitle
    if enabled:
        toggleStr = toggleStr + ' erfolgreich deaktiviert.'
    else:
        toggleStr = toggleStr + ' erfolgreich aktiviert.'
    await query.edit_message_text(toggleStr)
    return ConversationHandler.END


async def deleteJob(update, context):
    query = update.callback_query
    qData = query.data
    jobNum = int(qData)
    jobTitle = context.user_data['cronJobs'][jobNum]['title']
    replyText = ('Soll Erinnerung #' + str(jobNum) + ':\n' + jobTitle +
                 '\n wirklich gelöscht werden?')

    keyboard = [[InlineKeyboardButton("Ja", callback_data=str(CNFRM_DEL))],
                [InlineKeyboardButton("Nein", callback_data=str(ABORT))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(replyText, reply_markup=reply_markup)
    return SAVE


async def saveDeletion(update, context):
    query = update.callback_query
    qData = query.data
    globalDB_var = context.bot_data['globalDB_var']
    chatId = context.user_data['chatId']
    jobNum = int(qData)
    jobTitle = context.user_data['cronJobs'][jobNum]['title']

    cronJobs = await AUD_deleteUserCronJobData(globalDB_var, chatId, jobNum)

    context.user_data['cronJobs'] = cronJobs
    deleteStr = 'Erinnerung #' + str(jobNum) + ': ' + jobTitle + ' erfolgreich gelöscht.'

    await query.edit_message_text(deleteStr)
    return ConversationHandler.END


async def selectJobType(update, context):
    query = update.callback_query
    qData = query.data
    # Create new job
    if 'editType' not in context.user_data:
        context.user_data['editType'] = 'new'
        context.user_data['newJobData'] = {}
        replyText = 'Bitte Erinnerungs-Art wählen.'
    # Edit job
    else:
        jobNum = int(qData)
        selectedJob = context.user_data['cronJobs'][jobNum]
        context.user_data['selectedJob'] = selectedJob
        context.user_data['jobEdits'] = {}

        replyText = 'Bisherige Erinnerungs-Art: '
        replyText = replyText + '\n Bitte Erinnerungs-Art für die aktualisierte Erinnerung wählen.'

    keyboard = [[InlineKeyboardButton("Fahrradvorhersage (1h)", callback_data=str(TYPE_BIKE))],
                [InlineKeyboardButton("Wettervorhersage (24h)", callback_data=str(TYPE_WEATHER))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text('Bitte Erinnerungs-Art wählen.', reply_markup=reply_markup)
    return ADDRESS


async def selectAddressMethod(update, context):
    query = update.callback_query
    qData = query.data
    if qData == str(TYPE_BIKE):
        typeStr = 'bike'
        typeStrTxt = 'Fahrradvorhersage'
    else:
        typeStr = 'weather'
        typeStrTxt = 'Wettervorhersage'
    context.user_data['selectedType'] = typeStr
    context.user_data['typeStrTxt'] = typeStrTxt

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['jobType'] = typeStr
        replyText = 'Ok, es wird eine Erinnerung mit ' + typeStrTxt + ' erstellt.'
    elif context.user_data['selectedJob']['jobType'] != typeStr:
        context.user_data['jobEdits']['jobType'] = typeStr
        replyText = 'Die Erinnerung wurde zu einer ' + typeStrTxt + ' geändert.'
    else:
        replyText = 'Ok, die Erinnerung bleibt eine ' + typeStrTxt + '.'

    replyText = replyText + '\n Wie soll eine Adresse für die Erinnerung gewählt werden?'

    keyboard = [[InlineKeyboardButton("Aus Liste wählen", callback_data=str(LIST_SEL))],
                [InlineKeyboardButton("Manuell eingeben", callback_data=str(MANUAL_SEL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(replyText, reply_markup=reply_markup)
    return ADDRESS


async def selectAddress(update, context):
    query = update.callback_query
    typeStrTxt = context.user_data['typeStrTxt']
    jobType = context.user_data['selectedType']

    if jobType in context.user_data['addresses']:
        addressData = context.user_data['addresses'][jobType]
    else:
        addressData = []

    if len(addressData) == 0:
        await query.edit_message_text('Es sind noch keine Adressen für die ' + typeStrTxt + ' gespeichert.')
        return ConversationHandler.END
    else:
        if context.user_data['editType'] == 'edit':
            adr = context.user_data['selectedJob']['addressData']
            if 'shortName' in adr:
                replyText = 'Derzeitige Adresse:\n "' + adr['shortName'] + '": ' + adr['address'] + '\n'
            else:
                replyText = 'Derzeitige Adresse:\n ' + adr['address'] + '\n'
        else:
            replyText = ''
        keyboard = []
        for ctr, address in enumerate(addressData):
            buttonText = '"' + address['shortName'] + '": ' + address['address']
            buttonCallback = 'Field_' + str(ctr)
            keyboard.append([InlineKeyboardButton(buttonText, callback_data=buttonCallback)])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.answer()
        await query.edit_message_text('Für welche der gespeicherten Adressen soll eine Erinnerung erstellt werden?',
                                      reply_markup=reply_markup)
        return SCH_WDAYS


async def enterAddress(update, context):
    query = update.callback_query
    if context.user_data['editType'] == 'edit':
        adr = context.user_data['selectedJob']['addressData']
        replyText = 'Derzeitige Adresse:\n ' + adr['address'] + '\n'
    else:
        replyText = ''
    replyText = replyText + 'Bitte die gewünschte Adresse inkl. PLZ und Ort senden.'
    await query.answer()
    await query.edit_message_text(text=replyText)
    return SCH_WDAYS


def getWDayQuery(update, context):
    if context.user_data['editType'] == 'edit':
        currentWDays = context.user_data['selectedJob']['cronData']['job']['schedule']['wdays']
        context.user_data['currentWDays'] = currentWDays
        currentWDayStr = scheduleDict2Str({'wdays': currentWDays, 'hours': [], 'minutes': []})
        replyText_curr = 'Derzeitige Tage für die Erinnerung: \n' + currentWDayStr
        context.user_data['currentWDayText'] = replyText_curr
    else:
        replyText_curr = ''
    keyboard = [[InlineKeyboardButton("An Wochentagen", callback_data=str(WD_WEEK))],
                [InlineKeyboardButton("Am Wochenende", callback_data=str(WD_WE))],
                [InlineKeyboardButton("Täglich", callback_data=str(WD_ALL))],
                [InlineKeyboardButton("Manuell eingeben", callback_data=str(MANUAL_SEL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    replyText_q = 'An welchen Tagen soll die Erinnerung ausgeführt werden?'
    return reply_markup, replyText_curr, replyText_q


async def selectWDays(update, context):
    query = update.callback_query
    qData = query.data
    selectedType = context.user_data['selectedType']
    chosenAddressIdx = int(qData.replace('Field_', ''))
    chosenAddress = context.user_data['addresses'][selectedType][chosenAddressIdx]

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['addressData'] = chosenAddress
    else:
        context.user_data['jobEdits']['addressData'] = chosenAddress
    replyText = ('Die Erinnerung wird für die Adresse "' + chosenAddress['address'] + '" in ' +
                 chosenAddress['coord']['place'] + ' erstellt.\n')

    reply_markup, replyText_curr, replyText_q = getWDayQuery(update, context)
    replyText = replyText + replyText_curr + '\n' + replyText_q
    await query.answer()
    await query.edit_message_text(text=replyText, reply_markup=reply_markup)
    return SCH_HOURS


async def readAddress_selectWDays(update, context):
    address = update.message.text
    selectedType = context.user_data['selectedType']
    typeStrTxt = context.user_data['typeStrTxt']
    coord = findLatLon(address)
    addressData = {'address': address, 'coord': coord}

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['addressData'] = addressData
    else:
        context.user_data['jobEdits']['addressData'] = addressData

    replyText = 'Die Erinnerung wird für die Adresse "' + address + '" in ' + coord['place'] + ' erstellt.\n'

    reply_markup, replyText_curr, replyText_q = getWDayQuery(update, context)
    replyText = replyText + replyText_curr + '\n' + replyText_q
    await update.message.reply_text(replyText, reply_markup=reply_markup)
    return SCH_HOURS


async def enterWDays(update, context):
    query = update.callback_query
    if context.user_data['editType'] == 'edit':
        replyText_curr = context.user_data['currentWDayText'] + '\n'
    else:
        replyText_curr = ''
    replyText = (replyText_curr + 'Bitte die gewünschten Tage kommagetrennt eingeben. Bsp: \n' +
                 'Mi,Fr,So')
    await query.answer()
    await query.edit_message_text(text=replyText)
    return SCH_HOURS


def getHourQuery(update, context):
    if context.user_data['editType'] == 'edit':
        currentHours = context.user_data['selectedJob']['cronData']['job']['schedule']['hours']
        currentMinutes = context.user_data['selectedJob']['cronData']['job']['schedule']['minutes']
        context.user_data['currentHours'] = currentHours
        context.user_data['currentMinutes'] = currentMinutes
        currentHoursMinutesStr = scheduleDict2Str({'wdays': [], 'hours': currentHours, 'minutes': currentMinutes})
        replyText_curr = 'Die Erinnerung wird zurzeit um ' + currentHoursMinutesStr + ' ausgeführt.'
        context.user_data['currentHoursMinutesText'] = replyText_curr
    else:
        replyText_curr = ''

    replyText_q = ('Bitte die Stunden, zu denen die Erinnerung ausgeführt werden soll als kommagetrennte ' +
                   'Zahlen eingeben. Bsp:\n 12,14,15')
    return replyText_curr, replyText_q


async def readWDays_enterHours(update, context):
    wDaysMsg = update.message.text
    dayNames = ['so', 'mo', 'di', 'mi', 'do', 'fr', 'sa']
    dayList = wDaysMsg.split(',')
    newWDays = []
    for day in dayList:
        dayLower = day.lower()
        if dayLower in dayNames:
            newWDays.append(dayNames.index(dayLower))
        else:
            replyText = ('"' + day + '" konnte nicht richtig gelesen werden. Bitte die gewünschten Tage noch einmal' +
                         ' korrekt kommagetrennt eingeben.')
            await update.message.reply_text(replyText)
            return SCH_HOURS

    newWDayStr = scheduleDict2Str({'wdays': newWDays, 'hours': [], 'minutes': []})

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['schedule'] = {}
        context.user_data['newJobData']['schedule']['wdays'] = newWDays
        replyText = 'Okay, die Ausführung der Erinnerung erfolgt ' + newWDayStr + '.'
    elif context.user_data['currentWDays'] != newWDays:
        context.user_data['jobEdits']['schedule'] = {} # todo: das hier irgendwie hoch integrieren?? oder doch erst in save das dict aufmachen?
        context.user_data['jobEdits']['schedule']['wdays'] = newWDays
        replyText = 'Okay, die Ausführung der Erinnerung wurde zu ' + newWDayStr + ' geändert.'
    else:
        replyText = 'Okay, die Erinnerung wird weiter ' + newWDayStr + ' ausgeführt.'

    replyText_curr, replyText_q = getHourQuery(update, context)
    replyText = replyText + '\n' + replyText_curr + '\n' + replyText_q
    await update.message.reply_text(replyText)
    return SCH_MIN

async def enterHours(update, context):
    query = update.callback_query
    qData = query.data
    if qData == str(WD_WEEK):
        newWDays = list(range(1, 6))
        replyTextWD = 'an Wochentagen'
    elif qData == str(WD_WE):
        newWDays = [6, 0]
        replyTextWD = 'an Wochenendtagen'
    else: # all days
        newWDays = list(range(7))
        replyTextWD = 'täglich'

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['wdays'] = newWDays
        replyText = 'Okay, die Ausführung der Erinnerung erfolgt ' + replyTextWD + '.'
    elif context.user_data['currentWDays'] != newWDays:
        context.user_data['jobEdits']['wdays'] = newWDays
        replyText = 'Okay, die Erinnerung wird jetzt ' + replyTextWD + ' ausgeführt.'
    else:
        replyText = 'Okay, die Erinnerung wird weiter ' + replyTextWD + ' ausgeführt.'

    replyText_curr, replyText_q = getHourQuery(update, context)

    replyText = replyText + '\n' + replyText_curr + '\n' + replyText_q
    await query.answer()
    await query.edit_message_text(text=replyText)
    return SCH_MIN


def getMinutesQuery(update, context):
    if context.user_data['editType'] == 'edit':
        newHours = context.user_data['newHours']
        currentMinutes = context.user_data['selectedJob']['cronData']['job']['schedule']['minutes']
        newHoursMinutesStr = scheduleDict2Str({'wdays': [], 'hours': newHours, 'minutes': currentMinutes})
        replyText_curr = 'Die aktualisierte Erinnerung wird um ' + newHoursMinutesStr + ' ausgeführt.'
        context.user_data['currentMinText'] = replyText_curr
    else:
        replyText_curr = ''

    keyboard = [[InlineKeyboardButton("Zur vollen Stunde", callback_data=str(MIN_0))],
                [InlineKeyboardButton("Viertel nach", callback_data=str(MIN_15))],
                [InlineKeyboardButton("Halb", callback_data=str(MIN_30))],
                [InlineKeyboardButton("Viertel vor", callback_data=str(MIN_45))],
                [InlineKeyboardButton("Manuell eingeben", callback_data=str(MANUAL_SEL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    replyText_q = 'Zu welchen Minuten soll die Erinnerung ausgeführt werden?'
    return reply_markup, replyText_curr, replyText_q


async def readHours_selectMin(update, context):
    hoursMsg = update.message.text
    hoursList = hoursMsg.split(',')
    newHours = []
    for hourStr in hoursList:
        hour = int(hourStr)
        if -1 < hour < 24:
            newHours.append(hour)
        else:
            replyText = ('"' + hourStr + '" konnte nicht richtig gelesen werden. Bitte die gewünschten Stunden noch ' +
                         ' einmal korrekt kommagetrennt eingeben.')
            await update.message.reply_text(replyText)
            return SCH_MIN

    newHoursStr = scheduleDict2Str({'wdays': [], 'hours': newHours, 'minutes': []})
    context.user_data['newHours'] = newHours

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['hours'] = newHours
        replyText = 'Okay, die Ausführung der Erinnerung erfolgt zu den Stunden ' + newHoursStr + '.'
    elif context.user_data['currentHours'] != newHours:
        context.user_data['jobEdits']['hours'] = newHours
        replyText = 'Okay, die Ausführung der Erinnerung wurde zu den Stunden ' + newHoursStr + ' geändert.'
    else:
        replyText = 'Okay, die Erinnerung wird weiter zu den Stunden ' + newHoursStr + ' ausgeführt.'

    reply_markup, replyText_curr, replyText_q = getMinutesQuery(update, context)
    replyText = replyText + '\n' + replyText_curr + '\n' + replyText_q
    await update.message.reply_text(replyText, reply_markup=reply_markup)
    return TITLE


async def enterTitle(update, context):
    query = update.callback_query
    qData = query.data
    # todo: das hier an minutes anpassen
    keyboard = [[InlineKeyboardButton("Zur vollen Stunde", callback_data=str(MIN_0))],
                [InlineKeyboardButton("Viertel nach", callback_data=str(MIN_15))],
                [InlineKeyboardButton("Halb", callback_data=str(MIN_30))],
                [InlineKeyboardButton("Viertel vor", callback_data=str(MIN_45))],
                [InlineKeyboardButton("Manuell eingeben", callback_data=str(MANUAL_SEL))]]
    if qData == str(MIN_0):
        newMinutes = [0]
        replyTextMin = 'zur vollen Stunde'
    elif qData == str(MIN_15):
        newMinutes = [15]
        replyTextMin = 'um Viertel nach'
    elif qData == str(MIN_30):
        newMinutes = [30]
        replyTextMin = 'um Halb'
    else: # all days
        newMinutes = [45]
        replyTextMin = 'um Viertel vor'

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['minutes'] = newMinutes
        replyText = 'Okay, die Ausführung der Erinnerung erfolgt ' + replyTextMin + '.'
    elif context.user_data['currentMinutes'] != newMinutes:
        context.user_data['jobEdits']['minutes'] = newMinutes
        replyText = 'Okay, die Erinnerung wird jetzt ' + replyTextMin + ' ausgeführt.'
    else:
        replyText = 'Okay, die Erinnerung wird weiter ' + replyTextMin + ' ausgeführt.'


async def enterMin(update, context):
    query = update.callback_query
    if context.user_data['editType'] == 'edit':
        replyText_curr = context.user_data['currentMinText'] + '\n'
    else:
        replyText_curr = ''
    replyText = (replyText_curr + 'Bitte die Minuten, zu denen die Erinnerung ausgeführt werden soll ' +
                 'als kommagetrennte Zahlen eingeben. Bsp:\n 15,34,50')
    await query.answer()
    await query.edit_message_text(text=replyText)
    return TITLE

async def readMin_enterTitle(update, context):
    minutesMsg = update.message.text
    minutesList = minutesMsg.split(',')
    newMinutes = []
    for minuteStr in minutesList:
        minute = int(minuteStr)
        if -1 < minute < 60:
            newMinutes.append(minute)
        else:
            replyText = ('"' + minuteStr + '" konnte nicht richtig gelesen werden. Bitte die gewünschten Minuten noch ' +
                         ' einmal korrekt kommagetrennt eingeben.')
            await update.message.reply_text(replyText)
            return TITLE

    newMinutesStr = scheduleDict2Str({'wdays': [], 'hours': [], 'minutes': newMinutes})
    context.user_data['newMinutes'] = newMinutes

    if context.user_data['editType'] == 'new':
        context.user_data['newJobData']['hours'] = newMinutes
        replyText = 'Okay, die Ausführung der Erinnerung erfolgt zu den Minuten ' + newMinutesStr + '.'
    elif context.user_data['currentMinutes'] != newMinutes:
        context.user_data['jobEdits']['minutes'] = newMinutes
        replyText = 'Okay, die Ausführung der Erinnerung wurde zu den Minuten ' + newMinutesStr + ' geändert.'
    else:
        replyText = 'Okay, die Erinnerung wird weiter zu den Minuten ' + newMinutesStr + ' ausgeführt.'


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
