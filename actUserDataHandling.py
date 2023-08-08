from gbMongoDB import getUserData, createUserEntry, updateUserEntry
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
    userData['addresses'][addressType] = newDict
    updateUserEntry(db, chatId, addresses=userData['addresses'])
    actUserDataNew = actUserDataStored
    actUserDataNew[chatId] = userData
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

def deep_update_pydantic(mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]) -> Dict[KeyType, Any]:
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update_pydantic(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping
