from objects import DeadLetter,User
import datetime
from ServerRequest import ServerRequest
from utils import split_url_and_last_segment


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

PROJECT = "pustananaccounting"
DLQ_SUB = "projects/pustananaccounting/subscriptions/sendToDeadLetterUI"
ORIGINAL_TOPIC = "projects/pustananaccounting/topics/<YOUR_ORIGINAL_TOPIC>"  # set this

subscriber = pubsub_v1.SubscriberClient()
publisher = pubsub_v1.PublisherClient()

def retryMessage(deadLetter: DeadLetter):
    response = subscriber.pull(request={"subscription": DLQ_SUB, "max_messages": 1})
    deadLetter.retryMessage()
    if not response.received_messages:
        return "No DLQ messages."

    rm = response.received_messages[0]
    msg = rm.message

    # Optionally strip Pub/Sub system attrs before republishing
    attrs = {k: v for k, v in msg.attributes.items() if not k.startswith("x-goog-pubsub-")}

    # Re-publish the original payload
    future = publisher.publish(ORIGINAL_TOPIC, msg.data, **attrs)
    future.result()  # wait for publish OK

    # Ack the DLQ message only after successful publish
    subscriber.acknowledge(request={"subscription": DLQ_SUB, "ack_ids": [rm.ack_id]})
    return f"Republished {msg.message_id} to {ORIGINAL_TOPIC}"

