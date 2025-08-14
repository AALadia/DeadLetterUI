from __future__ import annotations
import os
from typing import Optional
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from utils import generateRandomString


def test_deadLetter():
    cwd = os.path.dirname(os.path.abspath(__file__))
    credentials = service_account.Credentials.from_service_account_file(
        os.path.join(cwd, "keys", "online-store-paperboy-f5f16aed6862.json"))
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

    #publish to createsalesorder topic
    topic_name = "createSalesOrder"
    data = {"_id": generateRandomString()}
    # convert to byte string
    data = str(data).encode("utf-8")
    future = publisher.publish('projects/online-store-paperboy/topics/' + topic_name, data=data)
    res = future.result()
    if res:
        print(f"Message published to {topic_name}: {res}")

if __name__ == "__main__":
    test_deadLetter()