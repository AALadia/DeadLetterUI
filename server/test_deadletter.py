from __future__ import annotations
import os
from typing import Optional
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from utils import generateRandomString
import json
import base64
from pubSub import PubSub,PubsubMessage
import time
from mongoDb import db


def test_deadLetter():
    cwd = os.path.dirname(os.path.abspath(__file__))
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(cwd, "keys", "online-store-paperboy-92adc6ce5dc5.json"))
    publisher = pubsub_v1.PublisherClient(credentials=credentials)

    #publish to createsalesorder topic
    topic_name = "createSalesOrder"
    data = {"_id": generateRandomString(),'customer':'test1'}
    dataId = data['_id']
    data = PubSub()._serialize_for_pubsub(data)
    data2 = {"_id": generateRandomString(),'customer':'test2'}
    data2Id = data2['_id']
    data2 = PubSub()._serialize_for_pubsub(data2)
    topicPath = 'projects/online-store-paperboy/topics/' + topic_name
    future = publisher.publish(topicPath,
                               data=data,
                                 originalTopicPath=topicPath,
                               )
    message1 = future.result()
    future = publisher.publish(topicPath,
                               data=data2,
                               )
    message2 = future.result()

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

        if retryCount > 10:
            raise Exception("Dead letter messages not found after 10 retries")

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
