"""No cloud database from anywhere but Cloud Run (localDbGuard.py, a copy
of create-star-app's).

The dead-letter database (mongoDb.db) is the production cluster's, from
DEADLETTER_MONGO_URI. Importing mongoDb opens no client to it; using it
needs Cloud Run (K_SERVICE/CLOUD_RUN_JOB) or ALLOW_PROD_DB_FROM_LOCAL=1, and
a test run never gets it. Each case runs in a child process whose pymongo
MongoClient is a recorder (no connection), with fake URIs; it runs with
--noconftest too.
"""
import json
import os
import subprocess
import sys

import pytest

import localDbGuard

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
FAKE_URI = 'mongodb://example.invalid:27017'

_CHILD = r'''
import json, os, unittest.mock
import pymongo, pymongo.mongo_client
hosts = []
def recorder(host=None, *args, **kwargs):
    hosts.append(host)
    return unittest.mock.MagicMock()
modules = [pymongo, pymongo.mongo_client]
try:
    import pymongo.synchronous.mongo_client as syncModule
    modules.append(syncModule)
except ImportError:
    pass
for module in modules:
    module.MongoClient = recorder
error = None
try:
    if os.environ.get('CHILD_IMPORTS_PYTEST'):
        import pytest
    import mongoDb
    exec(os.environ.get('CHILD_ACTION', ''))
except Exception as exc:
    error = {'type': type(exc).__name__, 'message': str(exc)}
print(json.dumps({'hosts': hosts, 'error': error}, default=str))
'''
_USE_DB = 'mongoDb.db.client'


def _runChild(action='', environment='localdev', extraEnv=None,
              importPytest=False, deadLetterUri=FAKE_URI):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('MONGO', 'DEADLETTER_')) and key not in
           (*localDbGuard.CLOUD_RUN_VARS, localDbGuard.OVERRIDE_VAR,
            'PYTEST_CURRENT_TEST')}
    env['ENVIRONMENT'] = environment
    env['CHILD_ACTION'] = action
    for name in ('MONGO_URI', 'MONGO_URI_CLOUDDEV', 'MONGO_URI_ACCOUNTING',
                 'MONGO_DUMP_URI'):
        env[name] = FAKE_URI
    if deadLetterUri is not None:
        env['DEADLETTER_MONGO_URI'] = deadLetterUri
    if importPytest:
        env['CHILD_IMPORTS_PYTEST'] = '1'
    env.update(extraEnv or {})
    completed = subprocess.run([sys.executable, '-c', _CHILD], cwd=SERVER_DIR,
                               env=env, capture_output=True, text=True,
                               timeout=300)
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _assertRefused(result):
    assert result['error'] is not None
    assert result['error']['type'] == 'AssertionError'
    assert 'non-local host' in result['error']['message']
    assert 'example.invalid' not in result['error']['message']
    assert FAKE_URI not in result['hosts']


def test_importingMongoDb_opensNoCloudClient():
    result = _runChild()

    assert result['error'] is None, result['error']
    assert result['hosts'], 'the recorder saw no client: the test proves nothing'
    assert FAKE_URI not in result['hosts']


def test_theDeadLetterDb_offCloudRun_isRefused():
    _assertRefused(_runChild(_USE_DB))


@pytest.mark.parametrize('extraEnv', [
    {'K_SERVICE': 'deadletter'}, {'CLOUD_RUN_JOB': 'fake-job'},
    {'ALLOW_PROD_DB_FROM_LOCAL': '1'}])
def test_theDeadLetterDb_onCloudRunOrWithTheOverride_connects(extraEnv):
    result = _runChild(_USE_DB, extraEnv=extraEnv)

    assert result['error'] is None, result['error']
    assert FAKE_URI in result['hosts']


@pytest.mark.parametrize('extraEnv', [
    {'K_SERVICE': 'deadletter'}, {'ALLOW_PROD_DB_FROM_LOCAL': '1'}])
def test_theDeadLetterDb_inATestRun_isRefused(extraEnv):
    _assertRefused(_runChild(_USE_DB, extraEnv=extraEnv, importPytest=True))


def test_theDeadLetterDb_withoutItsUri_failsClearly():
    result = _runChild(_USE_DB, extraEnv={'K_SERVICE': 'deadletter'},
                       deadLetterUri=None)

    assert result['error'] is not None
    assert ('DEADLETTER_MONGO_URI environment variable is not set'
            in result['error']['message'])


@pytest.mark.parametrize('environment, variable', [
    ('cloudprod', 'MONGO_URI'), ('clouddev', 'MONGO_URI_CLOUDDEV')])
def test_aCloudEnvironment_onCloudRun_connectsToItsCluster(environment,
                                                          variable):
    action = "mongoDb.mongoDb()"
    onCloudRun = _runChild(action, environment=environment,
                           extraEnv={'K_SERVICE': 'deadletter'})
    offCloudRun = _runChild(action, environment=environment)

    assert onCloudRun['error'] is None, onCloudRun['error']
    assert FAKE_URI in onCloudRun['hosts']
    _assertRefused(offCloudRun)


def test_mongoDb_commitsNoConnectionString():
    with open(os.path.join(SERVER_DIR, 'mongoDb.py'), encoding='utf-8') as file:
        assert 'mongodb+srv://' not in file.read()
