from gbMongoDB import getUserData, createUserEntry, updateUserEntry
from gbCronJobs import createJob, updateJob, deleteJob
import os.path
import pickle
from typing import Any, Dict, TypeVar
KeyType = TypeVar('KeyType')

def AUD_addUserData(db, actUserData, chatId, **dataEntries):
    userData = getUserData(db, chatId)
    if len(userData) == 0:
        createUserEntry(db, chatId, **dataEntries)
    else:
        for dataKey, dataEntry in dataEntries.items():
            if dataKey not in userData or dataEntry != userData[dataKey]:
                updateUserEntry(db, chatId, **{dataKey: dataEntry})
    userDataNew = getUserData(db, chatId)
    actUserDataStored = getUserDataPickle()
    actUserData = deep_update_pydantic(actUserData, actUserDataStored)
    if chatId not in actUserData:
        actUserData[chatId] = userData
    else:
        actUserData[chatId] = deep_update_pydantic(actUserData[chatId], userDataNew)
    saveUserDataPickle(actUserData)
    return actUserData

def AUD_updateUserAddressData(db, chatId, addressType, newDict):
    actUserDataStored = getUserDataPickle()
    userData = actUserDataStored[chatId]
    if 'addresses' in userData:
        # if addressType in userData['addresses']:
        #     userData['addresses'][addressType] = newDict
        # else:
        userData['addresses'][addressType] = newDict
    else:
        userData['addresses'] = {addressType: newDict}

    updateUserEntry(db, chatId, addresses=userData['addresses'])
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId] = userData
    saveUserDataPickle(actUserDataNew)

def AUD_addUserCronJobData(db, chatId, url, enabled, title, schedule):
    actUserDataStored = getUserDataPickle()
    userData = actUserDataStored[chatId]
    jobId = createJob(url, enabled, title, schedule)
    if 'cronJobs' in userData:
        allJobs = userData['cronJobs']
    else:
        allJobs = []
    jobNum = len(allJobs)
    cronTitle = str(chatId) + '-' + str(jobNum).zfill(3)
    jobDict = {'cronID': jobId, 'title': title, 'cronData': {'job': {
                'url': url,
                'enabled': enabled,
                'title': cronTitle,
                'saveResponses': False,
                'schedule': schedule
                }}}
    allJobs.append(jobDict)
    updateUserEntry(db, chatId, cronJobs=allJobs)
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId]['cronJobs'] = allJobs
    saveUserDataPickle(actUserDataNew)
    return jobNum

def AUD_updateUserCronJobData(db, chatId, jobNum, **dataEntries):
    actUserDataStored = getUserDataPickle()
    allJobs = actUserDataStored[chatId]['cronJobs']
    jobDict = allJobs[jobNum]
    jobId = jobDict[jobNum]['jobId']
    for dataKey, dataEntry in dataEntries.items():
        if dataKey in jobDict['cronData']['job']:
            jobDict['cronData']['job'][dataKey] = dataEntry
            updateJob(jobId, dataKey, dataEntry)
        else:
            jobDict[dataKey] = dataEntry
    allJobs[jobNum] = jobDict
    updateUserEntry(db, chatId, cronJobs=allJobs)
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId]['cronJobs'] = allJobs
    saveUserDataPickle(actUserDataNew)

def AUD_deleteUserCronJobData(db, chatId, jobNum):
    actUserDataStored = getUserDataPickle()
    allJobs = actUserDataStored[chatId]['cronJobs']
    jobId = allJobs[jobNum]['jobId']

    del allJobs[jobNum]
    deleteJob(jobId)

    updateUserEntry(db, chatId, cronJobs=allJobs)
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId]['cronJobs'] = allJobs
    saveUserDataPickle(actUserDataNew)

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
