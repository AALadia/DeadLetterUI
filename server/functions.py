from objects import DeadLetter,User
import datetime
from ServerRequest import ServerRequest
from utils import split_url_and_last_segment


def retryMessage(deadLetter: DeadLetter) -> DeadLetter:
    deadLetter.retryMessage()

    base_url, last_segment = split_url_and_last_segment(deadLetter.endpoint)

    serverRequest = ServerRequest(serverBaseUrl=base_url,
                                  headers={"Content-Type": "application/json"})
    try:
        res = serverRequest.post(last_segment, payload={'message': deadLetter.originalMessage})
        deadLetter.markAsSuccess()
    except Exception as e:
        deadLetter.markAsFailed(str(e))

    return deadLetter
