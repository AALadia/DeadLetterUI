from __future__ import annotations
import os
from typing import Optional
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from utils import generateRandomString
import json
import base64
from pubSub import PubSub,testPubSub
import time
from mongoDb import db


def test_deadLetter():

    #publish to createsalesorder topic
    topic_name = "createSalesOrder"
    data = {"_id": generateRandomString(),'customer':'test1'}
    dataId = data['_id']
    data2 = {"_id": generateRandomString(),'customer':'test2'}
    data2Id = data2['_id']
    testPubSub.publishMessage(data, topicName=topic_name,test=True)
    testPubSub.publishMessage(data2, topicName=topic_name,test=True)

    initiallyLoaded = False
    retryCount = 0
    while True:
        retryCount += 1
        if initiallyLoaded == False:
            print('WAITING 2 minutes for message to flow to dead letter service database')
            initiallyLoaded = True
            time.sleep(120)
        else:
            print('CHECKING DATABASE')
            time.sleep(5)

        maxRetry = 20
        if retryCount > maxRetry:
            raise Exception(f"Dead letter messages not found after {maxRetry} retries")

        found1 = db.read({"originalMessage._id": dataId}, "DeadLetters", findOne=True
        )
        found2 = db.read({"originalMessage._id": data2Id}, "DeadLetters", findOne=True
        )

        if found1 and found2:
            db.delete({"originalMessage._id": dataId}, "DeadLetters")
            db.delete({"originalMessage._id": data2Id}, "DeadLetters")
            break

if __name__ == "__main__":
    test_deadLetter()
