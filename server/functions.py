from objects import DeadLetter, User
import datetime
from ServerRequest import ServerRequest
from utils import split_url_and_last_segment
from pubSub import PubSub
import os
from google.oauth2 import service_account
import json
from pubSub import PubsubMessage

# def retryMessage(deadLetter: DeadLetter) -> DeadLetter:
#     deadLetter.retryMessage()

#     base_url, last_segment = split_url_and_last_segment(deadLetter.endpoint)

#     serverRequest = ServerRequest(serverBaseUrl=base_url,
#                                   headers={"Content-Type": "application/json"})
#     try:
#         res = serverRequest.post(last_segment, payload={'message': deadLetter.originalMessage})
#         deadLetter.markAsSuccess()
#     except Exception as e:
#         deadLetter.markAsFailed(str(e))

#     return deadLetter

# pip install google-cloud-pubsub
from google.cloud import pubsub_v1


cwd = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(cwd, "keys", "starpack-b149d-ea86f6d0c9ec.json")
credentials = service_account.Credentials.from_service_account_file(key_path)
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
publisher = pubsub_v1.PublisherClient(credentials=credentials)


def retryMessage(deadLetter: DeadLetter):
    attrs = {
                'publisherProjectId': deadLetter.publisherProjectId,
                'publisherProjectName': deadLetter.publisherProjectName,
                'topicName': deadLetter.topicName,
            }
    res = publisher.publish(deadLetter.publisherName,json.dumps(deadLetter.originalMessage).encode("utf-8"))
    result = res.result()
    deadLetter.retryMessage()
    if not result.received_messages:
        return "No DLQ messages."

    rm = result.received_messages[0]
    msg = rm.message

    # Optionally strip Pub/Sub system attrs before republishing
    attrs = {
        k: v
        for k, v in msg.attributes.items()
        if not k.startswith("x-goog-pubsub-")
    }

    # Re-publish the original payload
    future = publisher.publish(ORIGINAL_TOPIC, msg.data, **attrs)
    future.result()  # wait for publish OK

    # Ack the DLQ message only after successful publish
    subscriber.acknowledge(request={
        "subscription": deadLetter.publisherName,
        "ack_ids": [rm.ack_id]
    })
    return f"Republished {msg.message_id} to {ORIGINAL_TOPIC}"
