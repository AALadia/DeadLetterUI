"""No cloud database from anywhere but Cloud Run.

mongoDb.py (and every script that builds its own MongoClient) goes through
this guard. A client to any host but localhost/127.0.0.1 is allowed only

- on Cloud Run: K_SERVICE (a service) or CLOUD_RUN_JOB (a job) is set, or
- with an explicit override, ALLOW_PROD_DB_FROM_LOCAL=1, for a deliberate
  run against a cloud database from this machine (a migration), or a
  process's own opt-in variable (optInVar, e.g. the sticker printer PC's),

and never in a test run (pytest imported, with or without conftest). So
ENVIRONMENT=cloudprod alone, run locally, is refused too. A client through a
proxy (pymongo's proxyHost option) counts as non-local: the proxy, not this
machine, resolves the host. A client built for a cloud ENVIRONMENT is refused
the same way, before its URI is read.

The refusal is an AssertionError, as conftest's is, and never quotes the
host: a URI carries its credentials.

conftest.py imports isLocalDbHost from here too. This module imports nothing
from the project and connects to nothing, so conftest can load it before
mongoDb builds its singletons.
"""
import os
import sys

LOCAL_DB_HOSTS = ('localhost', '127.0.0.1')
# Set by Cloud Run in every service container and every job execution.
CLOUD_RUN_VARS = ('K_SERVICE', 'CLOUD_RUN_JOB')
# The explicit override for a deliberate cloud run from this machine.
OVERRIDE_VAR = 'ALLOW_PROD_DB_FROM_LOCAL'


def isLocalDbHost(host) -> bool:
    if host is None:
        return True  # pymongo's default: localhost:27017
    hosts = [host] if isinstance(host, str) else list(host)
    for entry in hosts:
        if not isinstance(entry, str):
            return False
        address = entry
        if address.startswith('mongodb://'):
            address = address[len('mongodb://'):]
        elif '://' in address:
            # mongodb+srv:// and anything else: never local
            return False
        # Credentials end at the LAST '@' before the path: an '@' in the
        # path or query ('...example.com/?appName=x@localhost') is not one.
        address = address.split('/', 1)[0].split('?', 1)[0].rsplit('@', 1)[-1]
        for node in address.split(','):
            if node.rsplit(':', 1)[0] not in LOCAL_DB_HOSTS:
                return False
    return True


def usesProxy(host, clientOptions=None) -> bool:
    if any(str(key).lower() == 'proxyhost' for key in (clientOptions or {})):
        return True
    hosts = [host] if isinstance(host, str) else list(host or [])
    return any(isinstance(entry, str) and '?' in entry and
               'proxyhost=' in entry.split('?', 1)[1].lower()
               for entry in hosts)


def isTestRun() -> bool:
    return 'pytest' in sys.modules


def isOnCloudRun() -> bool:
    return any(os.environ.get(name) for name in CLOUD_RUN_VARS)


def isCloudDbAllowed(optInVar=None) -> bool:
    """Whether this process may build a client to a cloud database."""
    if isTestRun():
        return False
    if isOnCloudRun() or os.environ.get(OVERRIDE_VAR) == '1':
        return True
    return optInVar is not None and os.environ.get(optInVar) == '1'


def _refuse(reason: str) -> None:
    raise AssertionError(
        f'refused a MongoDB client to a non-local host: {reason}. Only Cloud '
        f'Run (K_SERVICE/CLOUD_RUN_JOB) or {OVERRIDE_VAR}=1 reaches a cloud '
        'database, and a test run never does')


def assertLocalDbHostAllowed(host, clientOptions=None, optInVar=None) -> None:
    """Refuse a non-local host, or a proxy, unless isCloudDbAllowed."""
    if isLocalDbHost(host) and not usesProxy(host, clientOptions):
        return
    if not isCloudDbAllowed(optInVar):
        _refuse('this is a test run' if isTestRun() else
                'this is not Cloud Run')


def assertCloudDbAllowed(optInVar=None) -> None:
    """Refuse a client for a cloud ENVIRONMENT (its cluster is never local)
    unless isCloudDbAllowed, before any cloud URI is read."""
    if not isCloudDbAllowed(optInVar):
        _refuse('a cloud ENVIRONMENT outside Cloud Run' if not isTestRun()
                else 'a test run never builds a client for a cloud '
                'ENVIRONMENT')
