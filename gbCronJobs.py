import os
import json
import requests

ENDPOINT = 'https://api.cron-job.org'
CRON_JOB_KEY = os.environ["CRON_JOB_KEY"]

headers = {
    'Authorization': 'Bearer ' + CRON_JOB_KEY,
    'Content-Type': 'application/json'
}

#https://docs.cron-job.org/rest-api.html

def getAllJobs():
    result = requests.get(ENDPOINT + '/jobs', headers=headers)  #, proxies=proxies)
    resultjsn = result.json()
    return resultjsn['jobs']

def createJob(url, enabled, title, schedule): #folder?
    payload = {
        'job': {
            'url': url,
            'enabled': enabled,
            'title': title,
            'saveResponses': False,
            'schedule': schedule
        }
    }
    result = requests.put(ENDPOINT + '/jobs', headers=headers, data=json.dumps(payload))  #), proxies=proxies)
    resultjsn = result.json()
    return resultjsn['jobId']
