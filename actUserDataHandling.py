from gbMongoDB import getUserData, createUserEntry, updateUserEntry

def AUD_addUserData(db, actUserData, chatId, **dataEntries):
    userData = getUserData(db, chatId)
    if len(userData) == 0:
        createUserEntry(db, chatId, **dataEntries)
    else:
        for dataKey, dataEntry in dataEntries.items():
            if dataKey not in userData or dataEntry != userData[dataKey]:
                updateUserEntry(db, chatId, **{dataKey: dataEntry})
    userDataNew = getUserData(db, chatId)
    return userDataNew
