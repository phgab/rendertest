from gbMongoDB import getUserData, createUserEntry, updateUserEntry
from gbCronJobs import createJob, updateJob, deleteJob
import os
import pickle
import json
import urllib.parse
from typing import Any, Dict, TypeVar
KeyType = TypeVar('KeyType')
cronFolderID = int(os.environ['CRON_FOLDER_ID'])


async def AUD_addUserData(db, actUserData, chatId, **dataEntries):
    userData = await getUserData(db, chatId)
    if len(userData) == 0:
        await createUserEntry(db, chatId, **dataEntries)
    else:
        for dataKey, dataEntry in dataEntries.items():
            if dataKey not in userData or dataEntry != userData[dataKey]:
                await updateUserEntry(db, chatId, **{dataKey: dataEntry})
    userDataNew = await getUserData(db, chatId)
    actUserDataStored = getUserDataPickle()
    actUserData = deep_update_pydantic(actUserData, actUserDataStored)
    if chatId not in actUserData:
        actUserData[chatId] = userData
    else:
        actUserData[chatId] = deep_update_pydantic(actUserData[chatId], userDataNew)
    saveUserDataPickle(actUserData)
    return actUserData


async def AUD_updateUserAddressData(db, chatId, addressType, newDict):
    actUserDataStored = getUserDataPickle()
    userData = actUserDataStored[chatId]
    if 'addresses' in userData:
        # if addressType in userData['addresses']:
        #     userData['addresses'][addressType] = newDict
        # else:
        userData['addresses'][addressType] = newDict
    else:
        userData['addresses'] = {addressType: newDict}

    await updateUserEntry(db, chatId, addresses=userData['addresses'])
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId] = userData
    saveUserDataPickle(actUserDataNew)


async def AUD_addUserCronJobData(db, chatId, jobType, addressData, title, schedule):
    actUserDataStored = getUserDataPickle()
    userData = actUserDataStored[chatId]
    if 'cronJobs' in userData:
        allJobs = userData['cronJobs']
    else:
        allJobs = []
    jobNum = len(allJobs)
    cronTitle = str(chatId) + '-' + str(jobNum).zfill(3)
    schedule['mdays'] = [-1]
    schedule['months'] = [-1]
    url = getJobURL(chatId, jobType, 'coord', addressData['coord'])
    jobId = await createJob(url, True, cronTitle, schedule)
    jobDict = {'cronID': jobId, 'title': title, 'jobType': jobType, 'addressData': addressData,
               'cronData': {
                   'job': {
                       'url': url,
                       'enabled': True,
                       'folderId': cronFolderID,
                       'title': cronTitle,
                       'saveResponses': False,
                       'schedule': schedule
                   }
               }
               }
    allJobs.append(jobDict)
    await updateUserEntry(db, chatId, cronJobs=allJobs)
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId]['cronJobs'] = allJobs
    saveUserDataPickle(actUserDataNew)
    return jobNum


def getJobURL(chatId, jobType, addressType, addressData):
    app_url_link = os.environ['APP_URL_LINK']
    if addressType == 'coord':
        addressData = json.dumps(addressData)
    paramsSubstring = urllib.parse.urlencode(
        {'chat_id': str(chatId),
         'reminderType': jobType,
         addressType: addressData})
    url_extension = '/activatereminder?'

    url = app_url_link + url_extension + urllib.parse.quote_plus(paramsSubstring)
    return url


async def AUD_updateUserCronJobData(db, chatId, jobNum, **dataEntries):
    actUserDataStored = getUserDataPickle()
    allJobs = actUserDataStored[chatId]['cronJobs']
    jobDict = allJobs[jobNum]
    jobId = jobDict[jobNum]['jobId']
    for dataKey, dataEntry in dataEntries.items():
        if dataKey in jobDict['cronData']['job']:
            jobDict['cronData']['job'][dataKey] = dataEntry
            await updateJob(jobId, dataKey, dataEntry)
        else:
            jobDict[dataKey] = dataEntry
    allJobs[jobNum] = jobDict
    await updateUserEntry(db, chatId, cronJobs=allJobs)
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId]['cronJobs'] = allJobs
    saveUserDataPickle(actUserDataNew)
    return allJobs


async def AUD_deleteUserCronJobData(db, chatId, jobNum):
    actUserDataStored = getUserDataPickle()
    allJobs = actUserDataStored[chatId]['cronJobs']
    jobId = allJobs[jobNum]['jobId']

    del allJobs[jobNum]
    await deleteJob(jobId)

    await updateUserEntry(db, chatId, cronJobs=allJobs)
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId]['cronJobs'] = allJobs
    saveUserDataPickle(actUserDataNew)
    return allJobs


def saveUserDataPickle(actUserData):
    pickle.dump(actUserData, open("actUserData", "wb"))


def getUserDataPickle():
    if os.path.isfile("actUserData"):
        actUserData = pickle.load(open("actUserData", "rb"))
    else:
        actUserData = {}
    return actUserData


def loadSingleUserData(chatId):
    actUserData = getUserDataPickle()
    return actUserData[chatId]


def listUserAddresses(chatId):
    userData = loadSingleUserData(chatId)
    if 'addresses' in userData:
        addressData = userData['addresses']
    else:
        addressData = []
    return addressData


def listUserCronJobs(chatId):
    userData = loadSingleUserData(chatId)
    if 'cronJobs' in userData:
        cronData = userData['cronJobs']
    else:
        cronData = []
    return cronData


def getChatId(update, context):
    chat_id = -1
    if update.message is not None:
        # from a text message
        chat_id = str(update.message.chat.id)
    elif update.callback_query is not None:
        # from a callback message
        chat_id = str(update.callback_query.message.chat.id)
    return chat_id


def deep_update_pydantic(mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]) -> Dict[KeyType, Any]:
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update_pydantic(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping
