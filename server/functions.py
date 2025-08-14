import base64
from objects import DeadLetter, User
import datetime
from ServerRequest import ServerRequest
from utils import split_url_and_last_segment
import os
from google.oauth2 import service_account
import json
from google.cloud import pubsub_v1
from mongoDb import db
from typing import Literal

cwd = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(cwd, "keys", "starpack-b149d-ea86f6d0c9ec.json")

try:
    credentials = service_account.Credentials.from_service_account_file(
        key_path)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
except Exception as e:
    publisher = pubsub_v1.PublisherClient()


def retryMessage(deadLetter: DeadLetter, localOrProd: Literal['local','prod']):
    deadLetter.retryMessage()
    subscriptionName = deadLetter.subscriberName.split('/')[-1]
    subscription_path = subscriber.subscription_path(
        deadLetter.publisherProjectId, subscriptionName)
    subscription = subscriber.get_subscription(subscription=subscription_path)
    base_url, last_segment = split_url_and_last_segment(
        subscription.push_config.push_endpoint)
    serverRequest = ServerRequest(serverBaseUrl=base_url,
                                  headers={"Content-Type": "application/json"})
    try:
        # convert to utf8 original message
        original_json = json.dumps(deadLetter.originalMessage,
                                   ensure_ascii=False,
                                   separators=(",", ":"))
        # Encode to UTF-8, then Base64, then ASCII string
        data_b64 = base64.b64encode(
            original_json.encode("utf-8")).decode("ascii")

        payload = {
            "message": {
                "data": data_b64,
                "attributes": {
                    "topicName": deadLetter.topicName,
                    "publisherProjectId": deadLetter.publisherProjectId,
                    "publisherProjectName": deadLetter.publisherProjectName
                }
            },
            "subscription": deadLetter.subscriberName
        }
        res = serverRequest.post(last_segment, payload=payload)

        if localOrProd == 'prod':
            deadLetter.markAsSuccess()

    except Exception as e:
        deadLetter.markAsFailed(str(e))

    return deadLetter


def _getAllUsersToSendDeadLetterCreationEmail() -> list[User]:
    """
    Retrieve all users that have the role flag canReceiveNewDeadLetterEmails=true.
    Converts resulting documents to User objects (skips malformed docs).
    """
    query = {
        "roles": {
            "$elemMatch": {
                "_id": "canReceiveNewDeadLetterEmails",
                "value": True
            }
        }
    }

    # Attempt common patterns of db.read. Adjust if your db wrapper differs.
    users = db.read(query,'Users')  # preferred: collection first

    toReturn = []
    for x in users:
        toReturn.append(User(**x))

    return toReturn

if __name__ == "__main__":
    # Example usage
    pass
