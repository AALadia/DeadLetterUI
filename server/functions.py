import base64
from objects import DeadLetter, User

from ServerRequest import ServerRequest
from utils import split_url_and_last_segment

import json
from pubSubPublisherAndSubscriber import subscriber
from mongoDb import db
from typing import Literal


def retryMessage(deadLetter: DeadLetter, localOrProd: Literal['local','prod']):
    deadLetter.retryMessage()
    base_url, last_segment = split_url_and_last_segment(
        deadLetter.endPoint)
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
            },
            "subscription": deadLetter.subscription
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
