import base64
from objects import DeadLetter, User
import datetime
from ServerRequest import ServerRequest
from utils import split_url_and_last_segment
from pubSub import PubSub
import os
from google.oauth2 import service_account
import json

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

try:
    credentials = service_account.Credentials.from_service_account_file(key_path)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
except Exception as e:
    subscriber = pubsub_v1.SubscriberClient()
    publisher = pubsub_v1.PublisherClient()

def retryMessage(deadLetter: DeadLetter):
    subscriptionName = deadLetter.subscriberName.split('/')[-1]
    subscription_path = subscriber.subscription_path(deadLetter.publisherProjectId, subscriptionName)
    subscription = subscriber.get_subscription(subscription=subscription_path)
    base_url, last_segment = split_url_and_last_segment(subscription.push_config.push_endpoint)
    serverRequest = ServerRequest(serverBaseUrl=base_url,
                                  headers={"Content-Type": "application/json"})
    try:
        # convert to utf8 original message
        original_json = json.dumps(deadLetter.originalMessage, ensure_ascii=False, separators=(",", ":"))
        # Encode to UTF-8, then Base64, then ASCII string
        data_b64 = base64.b64encode(original_json.encode("utf-8")).decode("ascii")

        payload = {"message": {"data": data_b64}}
        res = serverRequest.post(last_segment, payload={'message': {"data": payload}})
        deadLetter.markAsSuccess()

    except Exception as e:
        deadLetter.markAsFailed(str(e))

    return deadLetter
    # attrs = {
    #             'publisherProjectId': deadLetter.publisherProjectId,
    #             'publisherProjectName': deadLetter.publisherProjectName,
    #             'topicName': deadLetter.topicName,
    #         }
    # res = publisher.publish(deadLetter.publisherName,json.dumps(deadLetter.originalMessage).encode("utf-8"), **attrs)
    # result = res.result()
    # deadLetter.retryMessage()

    # return deadLetter
