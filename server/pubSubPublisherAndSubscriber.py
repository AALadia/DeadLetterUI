import os
from google.oauth2 import service_account
from google.cloud import pubsub_v1

cwd = os.path.dirname(os.path.abspath(__file__))

# Map each project ID to its service account key file
_PROJECT_KEYS = {
    "starpack-b149d":
    os.path.join(cwd, "keys", "starpack-b149d-ea86f6d0c9ec.json"),
    "online-store-paperboy":
    os.path.join(cwd, "keys", "online-store-paperboy-92adc6ce5dc5.json"),
}

# Cache so we only create clients once per project
_client_cache: dict[str, tuple[pubsub_v1.PublisherClient,
                               pubsub_v1.SubscriberClient]] = {}


def get_clients_for_project(
    project_id: str
) -> tuple[pubsub_v1.PublisherClient, pubsub_v1.SubscriberClient]:
    """Return (publisher, subscriber) clients using the correct credentials for the given project."""
    if project_id in _client_cache:
        return _client_cache[project_id]

    key_path = _PROJECT_KEYS.get(project_id)
    if key_path and os.path.exists(key_path):
        credentials = service_account.Credentials.from_service_account_file(
            key_path)
        pub = pubsub_v1.PublisherClient(credentials=credentials)
        sub = pubsub_v1.SubscriberClient(credentials=credentials)
    else:
        # Fallback to default credentials
        pub = pubsub_v1.PublisherClient()
        sub = pubsub_v1.SubscriberClient()

    _client_cache[project_id] = (pub, sub)
    return pub, sub


# Default clients (starpack) for backward compatibility
key_path = _PROJECT_KEYS.get("starpack-b149d")

try:
    credentials = service_account.Credentials.from_service_account_file(
        key_path)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
except Exception as e:
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
