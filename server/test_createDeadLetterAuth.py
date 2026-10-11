"""createDeadLetter takes a dead letter only from the dead-letter
subscription's push, and replays it to production by itself only then.

Covers, through the real appPubSub.createDeadLetter handler,
PubSubRequests.createDeadLetter and callerAuth.py:
  - an anonymous POST, a token from any other account (this service's own
    replay account included), or one minted for another URL, is a 401 that
    stores nothing and mints no token;
  - the dead-letter subscription's token (the Pub/Sub push account, for this
    URL) stores the dead letter and replays it;
  - report mode stores an unverified dead letter but never replays it with
    a token (it emails it instead); localdev, likewise;
  - the email escapes everything the push sent.

No network, no database, no GCP: the modules that would reach them
(mongoDb connects to the production cluster on import) are replaced in
sys.modules before the handler is imported, and Google's certs are served
from a key pair made here.
"""
import base64
import json
import sys
import time
import types

import flask
import pytest

import callerAuth
import replayAuth

HOST = 'deadletter-376095984666.asia-east1.run.app'
URL = f'https://{HOST}/createDeadLetter'
KEY_ID = 'test-key'
PUSH_ACCOUNT = 'starpack-b149d@appspot.gserviceaccount.com'
REPLAY_ACCOUNT = '376095984666-compute@developer.gserviceaccount.com'
TOPIC = 'projects/starpack-b149d/topics/createUnit_accounting'

_keys = {}


def _keyPair():
    if not _keys:
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            key = rsa.generate_private_key(public_exponent=65537,
                                           key_size=2048)
            private = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption())
            public = key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.PKCS1)
        except ImportError:
            import rsa
            public, private = rsa.newkeys(2048)
            private, public = private.save_pkcs1(), public.save_pkcs1()
        _keys['private'] = private.decode()
        _keys['public'] = public.decode()
    return _keys['private'], _keys['public']


def _token(**overrides):
    from google.auth import crypt, jwt
    now = int(time.time())
    claims = {
        'iss': 'https://accounts.google.com',
        'aud': URL,
        'email': PUSH_ACCOUNT,
        'email_verified': True,
        'iat': now,
        'exp': now + 3600,
    }
    claims.update(overrides)
    signer = crypt.RSASigner.from_string(_keyPair()[0], key_id=KEY_ID)
    return jwt.encode(signer, claims).decode()


class _Db:

    def __init__(self):
        self.created = []

    def read(self, query, collection, findOne=False):
        return None

    def create(self, document, collection):
        self.created.append((collection, document))
        return document


def _module(name, **attrs):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    return module


@pytest.fixture
def deadLetters(monkeypatch):
    """The real handler, its collaborators recorded instead of run."""
    db = _Db()
    replays, mails, minted = [], [], []

    def createDeadLetterObject(id, messageId, originalMessage,
                               originalTopicPath):
        return types.SimpleNamespace(
            originalTopicPath=originalTopicPath,
            publisherProjectId=originalTopicPath.split('/')[1],
            model_dump=lambda by_alias: {
                '_id': messageId,
                'originalMessage': originalMessage
            })

    def routeConfig(**meta):

        def decorator(func):
            for key, value in meta.items():
                setattr(func, key, value)
            return func

        return decorator

    stubs = {
        'mongoDb':
        _module('mongoDb', db=db, mongoDb=object),
        'pubSub':
        _module('pubSub',
                decodeMessage=lambda data: json.loads(base64.b64decode(data))),
        'pubSubPublisherAndSubscriber':
        _module('pubSubPublisherAndSubscriber', publisher=None),
        'emailSender':
        _module('emailSender',
                send_mail=lambda to, subject, body: mails.append(body)),
        'functions':
        _module('functions',
                _replayDeadLetter=lambda *args: replays.append(args),
                _getAllUsersToSendDeadLetterCreationEmail=lambda: [
                    types.SimpleNamespace(email='staff@example.com')
                ]),
        'builderObjects':
        _module('builderObjects',
                createDeadLetterObject=createDeadLetterObject),
        'route_config':
        _module('route_config', route_config=routeConfig),
        'ApiRequests':
        _module('ApiRequests', DeadLetterActions=object),
    }
    for name, stub in stubs.items():
        monkeypatch.setitem(sys.modules, name, stub)
    for name in ('PubSubRequests', 'appPubSub'):
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(replayAuth, 'fetchIdToken',
                        lambda audience: minted.append(audience) or 'token')

    import appPubSub
    assert sys.modules['mongoDb'] is stubs['mongoDb']

    monkeypatch.setenv('ENVIRONMENT', 'cloudprod')
    monkeypatch.delenv(callerAuth.MODE_ENV, raising=False)
    monkeypatch.delenv(callerAuth.REPORT_UNTIL_ENV, raising=False)
    monkeypatch.setattr(callerAuth, '_fetchCerts',
                        lambda: {KEY_ID: _keyPair()[1]})
    monkeypatch.setattr(callerAuth, '_certsCache', {
        'certs': None,
        'fetchedAt': None,
        'attemptedAt': None
    })

    app = flask.Flask(__name__)
    app.register_blueprint(appPubSub.main)
    return types.SimpleNamespace(client=app.test_client(),
                                 db=db,
                                 replays=replays,
                                 mails=mails,
                                 minted=minted)


def _push(deadLetters, token=None, payload=None):
    message = payload or {'unitId': 'u1'}
    body = {
        'message': {
            'data': base64.b64encode(json.dumps(message).encode()).decode(),
            'attributes': {
                'originalTopicPath': TOPIC
            },
            'messageId': 'm1',
        }
    }
    headers = {} if token is None else {'Authorization': f'Bearer {token}'}
    return deadLetters.client.post('/createDeadLetter',
                                   json=body,
                                   headers=headers,
                                   base_url=f'https://{HOST}')


def _deadLettersStored(deadLetters):
    return [doc for collection, doc in deadLetters.db.created
            if collection == 'DeadLetters']


def test_theDeadLetterSubscriptionsPush_isStoredAndReplayed(deadLetters):
    response = _push(deadLetters, _token())

    assert response.status_code == 200
    assert [doc['_id'] for doc in _deadLettersStored(deadLetters)] == ['m1']
    assert deadLetters.replays == [('m1', 'prod', None)]
    assert deadLetters.mails == []


@pytest.mark.parametrize('token', [
    None,
    'not-a-token',
], ids=['anonymous', 'garbage'])
def test_aPushWithoutAValidToken_isRefused(deadLetters, token):
    response = _push(deadLetters, token)

    assert response.status_code == 401
    assert deadLetters.db.created == []
    assert deadLetters.replays == []
    assert deadLetters.minted == []


@pytest.mark.parametrize('overrides', [
    {'email': REPLAY_ACCOUNT},
    {'email': 'attacker@evil-project.iam.gserviceaccount.com'},
    {'aud': 'https://ecommerce-ez47324aua-de.a.run.app/createDeadLetter'},
    {'aud': f'https://{HOST}/somethingElse'},
], ids=['replayAccount', 'otherAccount', 'otherHost', 'otherPath'])
def test_aTokenNotFromTheDeadLetterSubscription_isRefused(
        deadLetters, overrides):
    response = _push(deadLetters, _token(**overrides))

    assert response.status_code == 401
    assert deadLetters.db.created == []
    assert deadLetters.replays == []
    assert deadLetters.minted == []


def test_onlyThePubSubPushAccount_mayCreateADeadLetter():
    assert callerAuth.PUSH_SERVICE_ACCOUNTS == (PUSH_ACCOUNT, )
    assert callerAuth.SERVICE_CALLER_ACCOUNTS == ()


def test_reportMode_storesAnUnverifiedDeadLetterButNeverReplaysIt(
        deadLetters, monkeypatch):
    monkeypatch.setenv(callerAuth.MODE_ENV, 'report')
    monkeypatch.setenv(callerAuth.REPORT_UNTIL_ENV, '2999-01-01')

    response = _push(deadLetters, _token(email=REPLAY_ACCOUNT))

    assert response.status_code == 200
    assert [doc['_id'] for doc in _deadLettersStored(deadLetters)] == ['m1']
    assert deadLetters.replays == []
    assert deadLetters.minted == []
    assert len(deadLetters.mails) == 1


def test_reportMode_stillReplaysAVerifiedPush(deadLetters, monkeypatch):
    monkeypatch.setenv(callerAuth.MODE_ENV, 'report')
    monkeypatch.setenv(callerAuth.REPORT_UNTIL_ENV, '2999-01-01')

    _push(deadLetters, _token())

    assert deadLetters.replays == [('m1', 'prod', None)]


def test_localdev_storesButNeverReplays(deadLetters, monkeypatch):
    monkeypatch.setenv('ENVIRONMENT', 'localdev')

    response = _push(deadLetters)

    assert response.status_code == 200
    assert deadLetters.replays == []


def test_outsideARequest_noAutoReplay():
    assert replayAuth.autoReplayAllowed() is False


def test_theEmail_escapesWhatThePushSent(deadLetters, monkeypatch):
    monkeypatch.setenv(callerAuth.MODE_ENV, 'report')
    monkeypatch.setenv(callerAuth.REPORT_UNTIL_ENV, '2999-01-01')

    _push(deadLetters, payload={'note': '<script>alert(1)</script>'})

    (body, ) = deadLetters.mails
    assert '<script>' not in body
    assert '&lt;script&gt;' in body


def test_everyCommittedPushHandler_requiresAPushCaller():
    import ast
    import pathlib
    tree = ast.parse(
        pathlib.Path(__file__).with_name('appPubSub.py').read_text(
            encoding='utf-8'))
    handlers = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        names = [ast.unparse(d) for d in node.decorator_list]
        routes = [i for i, n in enumerate(names) if n.startswith('main.route(')]
        if routes:
            below = names[routes[0] + 1:routes[0] + 2]
            handlers[node.name] = below == ['requirePushCaller']
    assert handlers == {'createDeadLetter': True}
