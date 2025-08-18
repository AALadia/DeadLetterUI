from __future__ import annotations
import os
from typing import Optional
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from utils import generateRandomString
import json
import base64
from pubSub import PubSub,PubsubMessage


def test_deadLetter():
    cwd = os.path.dirname(os.path.abspath(__file__))
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(cwd, "keys", "online-store-paperboy-92adc6ce5dc5.json"))
    publisher = pubsub_v1.PublisherClient(credentials=credentials)

    #publish to createsalesorder topic
    topic_name = "createSalesOrder"
    data = {"_id": generateRandomString(),'customer':'ladidadi'}
    data = PubSub()._serialize_for_pubsub(data)
    topicPath = 'projects/online-store-paperboy/topics/' + topic_name
    # future = publisher.publish(topicPath,
    #                            data=data,
    #                              originalTopicPath=topicPath,
    #                            )
    # res = future.result()
    future = publisher.publish(topicPath,
                               data=data,
                               )
    res = future.result()
    if res:
        print(f"Message published to {topic_name}: {res}")


if __name__ == "__main__":
    test_deadLetter()
