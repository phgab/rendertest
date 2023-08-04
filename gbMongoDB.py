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
    indexesData = db.users.getIndexes()
    currentIndices = [i[0] for i in [list(index['key'].keys()) for index in indexesData]]
    if 'chatID' not in currentIndices:
        db.users.create_index([("chatID", ASCENDING)], unique=True)


