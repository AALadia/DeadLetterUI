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
              importPytest=False, deadLetterUri=FAKE_URI, cloudUris=True):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('MONGO', 'DEADLETTER_')) and key not in
           (*localDbGuard.CLOUD_RUN_VARS, localDbGuard.OVERRIDE_VAR,
            'PYTEST_CURRENT_TEST')}
    env['ENVIRONMENT'] = environment
    env['CHILD_ACTION'] = action
    for name in ('MONGO_URI', 'MONGO_URI_CLOUDDEV', 'MONGO_URI_ACCOUNTING',
                 'MONGO_DUMP_URI') if cloudUris else ():
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


@pytest.mark.parametrize('environment', ['cloudprod', 'clouddev'])
def test_aCloudEnvironment_offCloudRun_isRefusedBeforeItsUriIsRead(
        environment):
    """With no cluster URI set at all, the refusal (not the missing
    variable) is what stops a cloud ENVIRONMENT off Cloud Run."""
    _assertRefused(_runChild('mongoDb.mongoDb()', environment=environment,
                             cloudUris=False))


def test_mongoDb_commitsNoConnectionString():
    with open(os.path.join(SERVER_DIR, 'mongoDb.py'), encoding='utf-8') as file:
        assert 'mongodb+srv://' not in file.read()


# The static gate: every script's own client goes through the guard.
_GUARD_EXEMPT_FILES = {'conftest.py', 'mongoDb.py', 'localDbGuard.py'}
_CLIENT_NAMES = {'MongoClient', 'AsyncMongoClient', 'AsyncIOMotorClient'}
_GUARD_NAME = 'assertLocalDbHostAllowed'
_SKIPPED_DIRS = {'venv', 'node_modules', '__pycache__', '_wt'}
_MUTATING_METHODS = {'update', 'setdefault', 'pop', 'popitem', 'clear',
                     '__setitem__', '__delitem__', 'append', 'extend',
                     'insert', 'remove'}


def _walkNoDefs(node):
    """ast.walk, without entering a nested function, lambda or class."""
    import ast
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        for child in ast.iter_child_nodes(current):
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                      ast.ClassDef, ast.Lambda)):
                stack.append(child)


def _annotationNodes(tree):
    import ast
    found = set()
    for node in ast.walk(tree):
        annotations = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations.append(node.returns)
        elif isinstance(node, (ast.arg, ast.AnnAssign)):
            annotations.append(node.annotation)
        for annotation in annotations:
            if annotation is not None:
                found.update(id(sub) for sub in ast.walk(annotation))
    return found


def _hostOf(call):
    for keyword in call.keywords:
        if keyword.arg == 'host':
            return keyword.value
    return call.args[0] if call.args else None


def _rebinds(node, host):
    """Whether node assigns to the host expression or to what it reads."""
    import ast
    targets = []
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign, ast.NamedExpr,
                           ast.For, ast.AsyncFor)):
        targets = [node.target]
    elif isinstance(node, (ast.With, ast.AsyncWith)):
        targets = [item.optional_vars for item in node.items
                   if item.optional_vars is not None]
    elif isinstance(node, ast.Delete):
        targets = node.targets
    readsEnvironment = 'os.environ' in host or 'os.getenv' in host
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        receiver = ast.unparse(node.func.value)
        if node.func.attr in _MUTATING_METHODS and (
                host == receiver or
                host.startswith((receiver + '.', receiver + '[')) or
                (readsEnvironment and receiver == 'os.environ')):
            return True
    for target in targets:
        for sub in ast.walk(target):
            if isinstance(sub, (ast.Name, ast.Attribute, ast.Subscript)):
                text = ast.unparse(sub)
                if text == host or host.startswith((text + '.', text + '[')):
                    return True
                if readsEnvironment and text.startswith('os.environ'):
                    return True
    return False


def _gateProblems(source):
    """Each client built in source for a host that is not a literal local
    host without localDbGuard.assertLocalDbHostAllowed(<that host>) as an
    earlier statement of the same function, with the host unchanged in
    between; and each indirect use of a client class (an alias passed on,
    getattr, functools.partial), which the gate cannot follow."""
    import ast
    tree = ast.parse(source)
    problems = []
    clientAliases = set(_CLIENT_NAMES)
    guardNames, guardModules = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in _CLIENT_NAMES:
                    clientAliases.add(alias.asname or alias.name)
                if node.module == 'localDbGuard' and alias.name == _GUARD_NAME:
                    guardNames.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'localDbGuard':
                    guardModules.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)) and
                node.name in guardNames | {_GUARD_NAME}):
            problems.append(f'{node.lineno}: defines its own {node.name}')
        targets = (node.targets if isinstance(node, ast.Assign) else
                   [node.target] if isinstance(node, (ast.AnnAssign,
                                                      ast.AugAssign)) else [])
        for target in targets:
            if (isinstance(target, ast.Name) and
                    target.id in guardNames | {_GUARD_NAME}):
                problems.append(f'{node.lineno}: rebinds {target.id}')

    def isClientRef(node):
        return ((isinstance(node, ast.Name) and node.id in clientAliases) or
                (isinstance(node, ast.Attribute) and
                 node.attr in _CLIENT_NAMES))

    def isGuardCall(node):
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        if isinstance(func, ast.Name):
            return func.id in guardNames
        return (isinstance(func, ast.Attribute) and func.attr == _GUARD_NAME
                and isinstance(func.value, ast.Name)
                and func.value.id in guardModules)

    annotations = _annotationNodes(tree)
    calledFuncs = {id(node.func) for node in ast.walk(tree)
                   if isinstance(node, ast.Call)}
    for node in ast.walk(tree):
        if id(node) in annotations:
            continue
        if (isClientRef(node) and id(node) not in calledFuncs and
                isinstance(getattr(node, 'ctx', None), ast.Load)):
            problems.append(
                f'{node.lineno}: indirect use of {ast.unparse(node)}')
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and
                node.func.id == 'getattr' and len(node.args) > 1 and
                isinstance(node.args[1], ast.Constant) and
                node.args[1].value in _CLIENT_NAMES):
            problems.append(f'{node.lineno}: getattr of {node.args[1].value}')
        if (isinstance(node, ast.Subscript) and
                isinstance(node.slice, ast.Constant) and
                node.slice.value in _CLIENT_NAMES):
            problems.append(f'{node.lineno}: lookup of {node.slice.value}')
        if isinstance(node, ast.Call) and isClientRef(node.func):
            if (any(keyword.arg is None for keyword in node.keywords) and
                    not any(keyword.arg == 'host'
                            for keyword in node.keywords)):
                problems.append(f'{node.lineno}: {ast.unparse(node.func)} '
                                'with ** keywords and no explicit host=')
            if node.args and isinstance(node.args[0], ast.Starred):
                problems.append(f'{node.lineno}: {ast.unparse(node.func)} '
                                'with a *-unpacked host')

    examined = set()
    functions = [tree, *[node for node in ast.walk(tree) if isinstance(
        node, (ast.FunctionDef, ast.AsyncFunctionDef))]]
    for function in functions:
        body = [statement for statement in function.body
                if not isinstance(statement, (ast.FunctionDef,
                                              ast.AsyncFunctionDef,
                                              ast.ClassDef))]
        for index, statement in enumerate(body):
            for call in _walkNoDefs(statement):
                if not (isinstance(call, ast.Call) and isClientRef(call.func)):
                    continue
                examined.add(id(call))
                host = _hostOf(call)
                if host is None or (isinstance(host, ast.Constant) and
                                    localDbGuard.isLocalDbHost(host.value)):
                    continue
                hostText = ast.unparse(host)
                guarded = False
                for earlier in range(index - 1, -1, -1):
                    candidate = body[earlier]
                    if (isinstance(candidate, ast.Expr) and
                            isGuardCall(candidate.value) and
                            _hostOf(candidate.value) is not None and
                            ast.unparse(_hostOf(candidate.value)) == hostText):
                        guarded = True
                        break
                    if any(_rebinds(node, hostText)
                           for node in _walkNoDefs(candidate)):
                        break
                if not guarded:
                    problems.append(
                        f'{call.lineno}: {ast.unparse(call.func)}({hostText}) '
                        'without an earlier unconditional '
                        f'{_GUARD_NAME}({hostText}) in the same function')
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isClientRef(node.func) and
                id(node) not in examined):
            problems.append(
                f'{node.lineno}: {ast.unparse(node.func)} built outside a '
                'function or module body the gate checks (a lambda, class '
                'body, default argument or decorator)')
    return problems


_GUARDED = ('from localDbGuard import assertLocalDbHostAllowed\n'
            'from pymongo import MongoClient\n')


@pytest.mark.parametrize('source, clean', [
    (_GUARDED + 'def f(uri):\n    assertLocalDbHostAllowed(uri)\n'
     '    MongoClient(uri)\n', True),
    ('import localDbGuard\nimport pymongo\n'
     'def f(uri):\n    localDbGuard.assertLocalDbHostAllowed(uri)\n'
     '    pymongo.MongoClient(host=uri)\n', True),
    ('from pymongo import MongoClient\nMongoClient("localhost", 27017)\n'
     'def f() -> MongoClient:\n    return MongoClient()\n', True),
    ('from pymongo import MongoClient\ndef f(uri):\n    MongoClient(host=uri)\n',
     False),
    ('from pymongo import MongoClient as MC\ndef f(uri):\n    MC(uri)\n', False),
    ('import pymongo\ndef f(uri):\n    getattr(pymongo, "MongoClient")(uri)\n',
     False),
    ('import functools\nfrom pymongo import MongoClient\n'
     'def f(uri):\n    functools.partial(MongoClient, uri)()\n', False),
    ('from motor.motor_asyncio import AsyncIOMotorClient\n'
     'def f(uri):\n    AsyncIOMotorClient(uri)\n', False),
    ('import pymongo as pm\ndef f(uri):\n    pm.MongoClient(uri)\n', False),
    ('from pymongo import AsyncMongoClient\n'
     'def f(uri):\n    AsyncMongoClient(uri)\n', False),
    ('from pymongo import MongoClient\nmake = lambda uri: MongoClient(uri)\n',
     False),
    ('from pymongo import MongoClient\nimport os\n'
     'class Holder:\n    client = MongoClient(os.environ["URI"])\n', False),
    ('from pymongo import MongoClient\nimport os\n'
     'def f(client=MongoClient(os.environ["URI"])):\n    pass\n', False),
    ('from pymongo import MongoClient\nimport os\n'
     '@decorate(MongoClient(os.environ["URI"]))\ndef f():\n    pass\n',
     False),
    (_GUARDED + 'def f(uri):\n    assertLocalDbHostAllowed(uri)\n'
     '    MongoClient(**{"host": uri})\n', False),
    ('import pymongo\ndef f(uri):\n    vars(pymongo)["MongoClient"](uri)\n',
     False),
    (_GUARDED + 'import os\n'
     'def f():\n    assertLocalDbHostAllowed(os.environ["URI"])\n'
     '    os.environ.update(URI="mongodb://elsewhere")\n'
     '    MongoClient(os.environ["URI"])\n', False),
    (_GUARDED + 'def f(args):\n    assertLocalDbHostAllowed(*args)\n'
     '    MongoClient(*args)\n', False),
    (_GUARDED + 'import os\n'
     'def f():\n    assertLocalDbHostAllowed(os.getenv("URI"))\n'
     '    os.environ.update(URI="mongodb://elsewhere")\n'
     '    MongoClient(os.getenv("URI"))\n', False),
    (_GUARDED + 'def f(uri):\n    assertLocalDbHostAllowed(uri)\n'
     '    uri = other()\n    MongoClient(uri)\n', False),
    (_GUARDED + 'def f(uri):\n    if False:\n'
     '        assertLocalDbHostAllowed(uri)\n    MongoClient(uri)\n', False),
    ('from pymongo import MongoClient\n'
     'def assertLocalDbHostAllowed(host):\n    pass\n'
     'def f(uri):\n    assertLocalDbHostAllowed(uri)\n    MongoClient(uri)\n',
     False),
    ('import other\nfrom pymongo import MongoClient\n'
     'def f(uri):\n    other.assertLocalDbHostAllowed(uri)\n'
     '    MongoClient(uri)\n', False),
    (_GUARDED + 'def f(uri):\n    assertLocalDbHostAllowed(uri)\n'
     '    def g(uri):\n        MongoClient(uri)\n', False),
], ids=['positional', 'hostKeyword', 'literalLocalAndAnnotation',
        'unguardedHostKeyword', 'alias', 'getattr', 'partial', 'motor',
        'moduleAlias', 'asyncClient', 'lambda', 'classBody', 'defaultArgument',
        'decoratorArgument', 'doubleStarHost', 'varsLookup',
        'environUpdatedAfterGuard', 'starredHost', 'getenvAfterEnvironUpdate',
        'reassignedAfterGuard', 'guardUnderIf', 'localStub',
        'guardOnAnotherModule', 'guardInOuterFunction'])
def test_theStaticGate_findsWhatItMust(source, clean):
    problems = _gateProblems(source)

    assert (problems == []) is clean, problems


def test_everyScriptsOwnMongoClient_goesThroughTheGuard():
    """A script anywhere in the repo that builds its own MongoClient (or
    AsyncMongoClient, or motor's AsyncIOMotorClient) for a host it was given
    (a --uri, an environment variable) calls
    localDbGuard.assertLocalDbHostAllowed(<that host>) first, unconditionally,
    in the same function: a cloud host then needs Cloud Run or
    ALLOW_PROD_DB_FROM_LOCAL=1 like every mongoDb client."""
    repoDir = os.path.dirname(SERVER_DIR)
    offenders = []
    for root, dirs, files in os.walk(repoDir):
        dirs[:] = [name for name in dirs
                   if name not in _SKIPPED_DIRS and not name.startswith('.')]
        for name in files:
            if (not name.endswith('.py') or name.startswith('test_') or
                    name in _GUARD_EXEMPT_FILES):
                continue
            path = os.path.join(root, name)
            with open(path, encoding='utf-8', errors='replace') as file:
                source = file.read()
            try:
                problems = _gateProblems(source)
            except SyntaxError:
                continue  # not this interpreter's Python: nothing to judge
            offenders.extend(f'{os.path.relpath(path, repoDir)}:{problem}'
                             for problem in problems)
    assert offenders == [], (
        'a MongoDB client the guard does not cover: ' + '; '.join(offenders))
