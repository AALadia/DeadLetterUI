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

    successfulEndpoints = []
    errors = []

    if endPoint is None:
        raise ValueError("Endpoint is None. Please update the dead letter object in MongoDB and update the endPoints : list[str]. To prevent this from happening again check the pubSub publish message function and add the key originalTopicPath to the attributes of the message.")

    for endPoint in deadLetter.endPoints:
        base_url, last_segment = split_url_and_last_segment(
            endPoint)
        serverRequest = ServerRequest(serverBaseUrl=base_url,
                                    headers={"Content-Type": "application/json"})
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
                "messageId" : deadLetter.messageId,
                "attributes" : {
                    "originalTopicPath": deadLetter.originalTopicPath,
                }
            },
            "subscription": ""
        }
        try:
            res = serverRequest.post(last_segment, payload=payload)
            successfulEndpoints.append(endPoint)
        except Exception as e:
            errors.append((endPoint, str(e)))

    if len(successfulEndpoints) == len(deadLetter.endPoints):
        if localOrProd == 'prod':
            deadLetter.markAsSuccess()
    else:
        errorString = ''
        for x in errors:
            errorString += f" - {x[0]}: {x[1]}\n"
        deadLetter.markAsFailed(errorString)

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
