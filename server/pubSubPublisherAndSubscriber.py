import os
from google.oauth2 import service_account
from google.cloud import pubsub_v1

cwd = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(cwd, "keys", "starpack-b149d-ea86f6d0c9ec.json")

try:
    credentials = service_account.Credentials.from_service_account_file(
        key_path)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
except Exception as e:
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()