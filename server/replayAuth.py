"""The ID token a production replay carries.

Every Star App push handler accepts only a Google-signed ID token whose
audience is the handler's own URL and whose email is in its callerAuth
PUSH_SERVICE_ACCOUNTS (Pub/Sub's push account, and this service's runtime
account for replays). "Retry Prod" therefore sends one, minted for the push
endpoint it replays to by the metadata server on Cloud Run. A local replay
(a URL typed in the dashboard) never gets one: a token is only ever sent to
the production endpoint it was minted for.

A new dead letter is also replayed to production by itself, from
createDeadLetter, but only when autoReplayAllowed(): the push that delivered
it carried the dead-letter subscription's OIDC token and callerAuth verified
it. Anything else (an anonymous POST, a replay token, a push that localdev or
report mode let through unverified) is stored and emailed, never replayed
with a token, so no one can have this service deliver a payload of their
choosing, with its token, to a topic's consumers. A staff member's "Retry
Prod" (replayDeadLetter, role-gated) is the only other path that mints one.
"""


def autoReplayAllowed() -> bool:
    """Whether createDeadLetter may replay the new dead letter to production
    with this service's token: only inside a push whose caller callerAuth
    verified."""
    from flask import has_request_context
    from callerAuth import callerVerified
    return has_request_context() and callerVerified()


def fetchIdToken(audience: str) -> str:
    import google.auth.transport.requests
    import google.oauth2.id_token
    return google.oauth2.id_token.fetch_id_token(
        google.auth.transport.requests.Request(), audience)


def replayHeaders(endPoint: str, localOrProd: str) -> dict:
    """The headers of a replay POST to `endPoint`."""
    headers = {"Content-Type": "application/json"}
    if localOrProd == 'prod':
        headers['Authorization'] = f'Bearer {fetchIdToken(endPoint)}'
    return headers
