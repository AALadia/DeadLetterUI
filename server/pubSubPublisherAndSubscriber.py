import os
import json
from google.oauth2 import service_account
from google.cloud import pubsub_v1

cwd = os.path.dirname(os.path.abspath(__file__))

# Load the online-store-paperboy key directly
_ONLINE_STORE_KEY_PATH = os.path.join(
    cwd, "online-store-paperboy-92adc6ce5dc5.json")
with open(_ONLINE_STORE_KEY_PATH) as f:
    _ONLINE_STORE_KEY_DATA = json.load(f)

_online_store_credentials = service_account.Credentials.from_service_account_info(
    _ONLINE_STORE_KEY_DATA)

# Cache so we only create clients once per project
_client_cache: dict[str, tuple[pubsub_v1.PublisherClient,
                               pubsub_v1.SubscriberClient]] = {}


def get_clients_for_project(
    project_id: str
) -> tuple[pubsub_v1.PublisherClient, pubsub_v1.SubscriberClient]:
    """Return (publisher, subscriber) using the correct credentials for the given project."""
    if project_id in _client_cache:
        return _client_cache[project_id]

    if project_id == "online-store-paperboy":
        pub = pubsub_v1.PublisherClient(credentials=_online_store_credentials)
        sub = pubsub_v1.SubscriberClient(credentials=_online_store_credentials)
    else:
        # Default credentials (works for the project the app is deployed in)
        pub = pubsub_v1.PublisherClient()
        sub = pubsub_v1.SubscriberClient()

    _client_cache[project_id] = (pub, sub)
    return pub, sub


# Default clients for backward compatibility
publisher, subscriber = get_clients_for_project("starpack-b149d")
