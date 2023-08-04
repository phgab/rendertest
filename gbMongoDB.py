import pymongo
from pymongo import MongoClient
import os

DBCONNCTSTR = os.environ["DBCONNCTSTR"]

dbClient = MongoClient(DBCONNCTSTR)

db = dbClient.teltest


def addTestUser():
    users = db.users
    testuser = {'id': 279, 'name': 'Gorg'}
    users.insert_one(testuser)
