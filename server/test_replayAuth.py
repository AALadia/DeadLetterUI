"""A production replay carries an ID token for the endpoint it replays to;
a local one never does. A refused replay shows the handler's message.

No network, no database."""
import pytest
import requests

import replayAuth
import ServerRequest as serverRequestModule
from ServerRequest import ServerRequest

ENDPOINT = 'https://ecommerce-abc123-de.a.run.app/updateUnit_accounting'


@pytest.fixture
def minted(monkeypatch):
    audiences = []

    def fetchIdToken(audience):
        audiences.append(audience)
        return 'id-token'

    monkeypatch.setattr(replayAuth, 'fetchIdToken', fetchIdToken)
    return audiences


def test_aProdReplay_carriesAnIdTokenForItsEndpoint(minted):
    headers = replayAuth.replayHeaders(ENDPOINT, 'prod')

    assert headers == {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer id-token'
    }
    assert minted == [ENDPOINT]


def test_aLocalReplay_carriesNoToken(minted):
    headers = replayAuth.replayHeaders('http://127.0.0.1:8000/fn', 'local')

    assert headers == {'Content-Type': 'application/json'}
    assert minted == []


def _refusedWith(monkeypatch, status, body):

    def post(url, json, headers, timeout):
        response = requests.models.Response()
        response.status_code = status
        response._content = body
        response.url = url
        return response

    monkeypatch.setattr(serverRequestModule.requests, 'post', post)
    with pytest.raises(ValueError) as info:
        ServerRequest('https://svc.example/', {}).post('fn', {})
    return str(info.value)


def test_aRefusedReplay_showsTheHandlersMessage(monkeypatch):
    assert _refusedWith(
        monkeypatch, 401,
        b'{"message": "Unauthorized", "status": 401}') == 'Unauthorized'


def test_aFailedReplay_stillShowsTheHandlersTraceback(monkeypatch):
    assert _refusedWith(
        monkeypatch, 500,
        b'{"message": "x", "traceback": "Traceback (error id 1)"}'
    ) == 'Traceback (error id 1)'


# ------------------- retryMessage: which replay carries one ------------------- #

LOCAL_ENDPOINT = 'http://127.0.0.1:8000/updateUnit_accounting'


@pytest.fixture
def retry(monkeypatch, minted):
    """functions.retryMessage with its database and GCP modules replaced
    (mongoDb connects to the production cluster on import), recording what
    each replay POST carried."""
    import sys
    import types

    class _ServiceErrorMessage:

        def __init__(self, **fields):
            self.__dict__.update(fields)

    stubs = {
        'objects':
        types.SimpleNamespace(DeadLetter=object,
                              User=object,
                              ServiceErrorMessage=_ServiceErrorMessage),
        'pubSubPublisherAndSubscriber':
        types.SimpleNamespace(subscriber=None),
        'mongoDb':
        types.SimpleNamespace(db=None),
    }
    for name, stub in stubs.items():
        monkeypatch.setitem(sys.modules, name, stub)
    monkeypatch.delitem(sys.modules, 'functions', raising=False)
    import functions
    assert sys.modules['mongoDb'] is stubs['mongoDb']

    posts = []

    def post(self, path, payload):
        posts.append({'base': self.serverBaseUrl, 'headers': self.headers})
        return {}

    monkeypatch.setattr(ServerRequest, 'post', post)

    def run(localOrProd, localEndpoint):
        deadLetter = types.SimpleNamespace(
            endPoints=[ENDPOINT],
            originalMessage={'unitId': 'u1'},
            messageId='m1',
            originalTopicPath='projects/p/topics/t',
            retryMessage=lambda: None,
            markAsSuccess=lambda: None,
            markAsFailed=lambda *args: None)
        functions.retryMessage(deadLetter, localOrProd, localEndpoint)
        return posts

    return run


def test_retryProd_sendsATokenForEachProductionEndpoint(retry, minted):
    (sent, ) = retry('prod', None)

    assert sent['headers'] == {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer id-token'
    }
    assert minted == [ENDPOINT]


@pytest.mark.parametrize('localOrProd', ['prod', 'local'])
def test_aReplayToATypedLocalEndpoint_neverCarriesAToken(
        retry, minted, localOrProd):
    (sent, ) = retry(localOrProd, LOCAL_ENDPOINT)

    assert sent['base'] == 'http://127.0.0.1:8000/'
    assert sent['headers'] == {'Content-Type': 'application/json'}
    assert minted == []
