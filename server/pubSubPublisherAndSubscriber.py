from google.cloud import pubsub_v1

# Every project's clients use Application Default Credentials: on Cloud Run,
# the deadletter service's own service account. Reading another project's
# topics (online-store-paperboy) needs that account to hold a Pub/Sub role
# there; no key file is committed or loaded.

# Cache so we only create clients once per project
_client_cache: dict[str, tuple[pubsub_v1.PublisherClient,
                               pubsub_v1.SubscriberClient]] = {}


def get_clients_for_project(
    project_id: str
) -> tuple[pubsub_v1.PublisherClient, pubsub_v1.SubscriberClient]:
    """Return (publisher, subscriber) for the given project, with the
    service's own credentials."""
    if project_id in _client_cache:
        return _client_cache[project_id]

    pub = pubsub_v1.PublisherClient()
    sub = pubsub_v1.SubscriberClient()

    _client_cache[project_id] = (pub, sub)
    return pub, sub


# Default clients for backward compatibility
publisher, subscriber = get_clients_for_project("starpack-b149d")
