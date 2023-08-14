import pymongo
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure
import os

DBCONNCTSTR = os.environ["DBCONNCTSTR"]

# functions to add
# getUserData - data for a single user defined by chatID (userID, name)
# addUserToList - global user list in main file, if chatID is not known
# updateUserData - if the user data has changed (checked every time on first interaction in runtime?) or the user actively asks for it(?)
# getUserCronJobData - return the cron job data for a specific user
# updateUserCronJobData

# add a .py file for the cron job management with functions:
# getUserCronJobs
# addUserCronJob
# deleteUserCronJob
# updateUserCronJobs


def getClientDB():
    client = MongoClient(DBCONNCTSTR)
    try:
        client.server_info()
    except ConnectionFailure:
        print('MongoDB connection failure')
    db = client.gbweatherbot
    ensureIndexSetup(db)
    return client, db


def ensureIndexSetup(db):
    # users collection
    try:
        indexesData = db.users.getIndexes()
        currentIndices = [i[0] for i in [list(index['key'].keys()) for index in indexesData]]
        if 'chatId' not in currentIndices:
            db.users.create_index([("chatId", ASCENDING)], unique=True)
    except:
        db.users.create_index([("chatId", ASCENDING)], unique=True)


async def getUserData(db, chatId):
    try:
        userData = db.users.find_one({'chatId': chatId})
        del userData['chatId']
        return userData
    except:
        return []


async def createUserEntry(db, chatId, **dataEntries):
    userData = {'chatId': chatId}
    for entryName, entryData in dataEntries.items():
        userData[entryName] = entryData
    db.users.insert_one(userData)


async def updateUserEntry(db, chatId, **dataEntries):
    userData = {entryName: entryData for entryName, entryData
                in dataEntries.items()}
    db.users.update_one({'chatId': chatId}, {'$set': userData})


