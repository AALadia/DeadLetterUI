import base64
from objects import DeadLetter, User

from ServerRequest import ServerRequest
from utils import split_url_and_last_segment

import json
from pubSubPublisherAndSubscriber import subscriber
from mongoDb import db
from typing import Literal


def _replayDevDataMessage(devDataId: str, endpoint: str) -> None:
    devData = db.read({'_id': devDataId}, 'DevData', findOne=True)
    if not devData:
        raise ValueError("DevData not found")
    retryMessage()
    # Logic to replay the DevData message


def _replayDeadLetter(
    deadLetterId: str,
    localOrProd: Literal['local', 'prod'],
    localEndpoint: str | None,
) -> dict:
    if localEndpoint == '':
        localEndpoint = None

    # Optional runtime guard (useful because Literal is not enforced at runtime)
    if localOrProd not in ('local', 'prod'):
        raise ValueError("localOrProd must be either 'local' or 'prod'")

    if localOrProd == 'local' and localEndpoint is None:
        raise ValueError(
            "localEndpoint must be provided when clicking 'Retry Local'")

    if localOrProd == 'prod' and localEndpoint is not None:
        raise ValueError(
            "localEndpoint should not be provided when clicking 'Retry Prod'")

    deadLetter = db.read({'_id': deadLetterId}, 'DeadLetters', findOne=True)
    deadLetter = DeadLetter(**deadLetter)
    deadLetter = retryMessage(deadLetter, localOrProd, localEndpoint)
    deadLetter = db.update(
        {
            '_id': deadLetter.id,
            '_version': deadLetter.version
        }, deadLetter.model_dump(by_alias=True), 'DeadLetters')

    if localOrProd == 'prod':
        if deadLetter['status'] == "failed":
            raise ValueError(
                deadLetter['errorMessage']
            )

    return deadLetter


def retryMessage(deadLetter: DeadLetter, localOrProd: Literal['local', 'prod'],
                 localEndpoint: str | None):
    deadLetter.retryMessage()

    successfulEndpoints = []
    errors = []

    if localOrProd == 'prod':
        if deadLetter.endPoints is None:
            raise ValueError(
                "Endpoints is None. Please update the dead letter object in MongoDB and update the key endPoints : list[str]. To prevent this from happening again check the pubSub publish message function and add the key originalTopicPath to the attributes of the message."
            )

    # we use localEndpoint if provided
    if localEndpoint is not None:
        endPoints = [localEndpoint]
    else:
        endPoints = deadLetter.endPoints

    for endPoint in endPoints:
        base_url, last_segment = split_url_and_last_segment(endPoint)
        serverRequest = ServerRequest(
            serverBaseUrl=base_url,
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
                "messageId": deadLetter.messageId,
                "attributes": {
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

    if deadLetter.endPoints is not None:
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
    users = db.read(query, 'Users')  # preferred: collection first

    toReturn = []
    for x in users:
        toReturn.append(User(**x))

    return toReturn


if __name__ == "__main__":
    # Example usage
    pass
