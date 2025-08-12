"""App / API / TypeScript generation utilities.
Cleaner refactor of the original AppCreator script.
"""
from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import types
import typing
import importlib.util  # added
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Union, get_args, get_origin
import datetime

from ApiRequests import ApiRequests
from PubSubRequests import PubSubRequests

# ----------------------------- Global Path Constants ----------------------------- #


def _compute_project_root(start: Path) -> Path:
    """Ascend directories until a .git folder (project root) is found or stop at filesystem root."""
    cur = start
    while True:
        if (cur / '.git').exists() or cur.parent == cur:
            return cur
        cur = cur.parent


PROJECT_ROOT: Path = _compute_project_root(Path(__file__).resolve().parent)
SERVER_DIR: Path = PROJECT_ROOT / 'server'
CLIENT_DIR: Path = PROJECT_ROOT / 'client'
CLIENT_DEADLETTER_DIR: Path = CLIENT_DIR / 'deadletter'
CLIENT_APP_DIR: Path = CLIENT_DEADLETTER_DIR / 'app'
CLIENT_SCHEMAS_DIR: Path = CLIENT_APP_DIR / 'schemas'
SERVER_SCHEMAS_DIR: Path = SERVER_DIR / 'schemas'
CLIENT_API_DIR: Path = CLIENT_APP_DIR / 'api'
OBJECTS_PY_PATH: Path = SERVER_DIR / 'objects.py'

# Ensure required directories exist where appropriate
CLIENT_SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
SERVER_SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_API_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------- Type Helpers ----------------------------- #

BASIC_PY_TO_TS: Dict[Any, str] = {
    int: "number",
    float: "number",
    str: "string",
    bool: "boolean",
    dict: "Record<string, any>",
    list: "any[]",
    Any: "any",
    type(None): "null",
    datetime.datetime: "Date",
}


def py_annotation_to_ts(ann: Any) -> str:
    """Convert a Python type annotation to a TypeScript type string."""
    if ann is inspect._empty:
        return "any"

    if ann in BASIC_PY_TO_TS:
        return BASIC_PY_TO_TS[ann]

    # typing constructs
    origin = get_origin(ann)
    args = get_args(ann) or ()

    # List / list
    if origin in (list, typing.List):
        return f"{py_annotation_to_ts(args[0]) if args else 'any'}[]"

    # Dict
    if origin in (dict, typing.Dict):
        if len(args) == 2:
            return f"Record<{py_annotation_to_ts(args[0])}, {py_annotation_to_ts(args[1])}>"
        return "Record<string, any>"

    # Tuple
    if origin in (tuple, typing.Tuple):
        if not args:
            return "any[]"
        if len(args) == 2 and args[1] is Ellipsis:
            return f"{py_annotation_to_ts(args[0])}[]"
        return f"[{', '.join(py_annotation_to_ts(a) for a in args)}]"

    # Union / Optional
    if origin in (typing.Union, types.UnionType):  # PEP 604 | support
        return " | ".join(py_annotation_to_ts(a) for a in args)

    # Forward ref as string
    if isinstance(ann, str):
        return ann

    # Fallback
    try:
        return ann.__name__
    except AttributeError:
        return "any"


# ----------------------------- Utility Classes ----------------------------- #


@dataclass
class Parameters:
    names: List[str] = field(default_factory=list)

    def as_assignment_block(self, indent: int = 8) -> str:
        if not self.names:
            return ""
        pad = " " * indent
        return "\n".join(f"{pad}{n} = data['{n}']" for n in self.names) + "\n"

    def comma_join(self) -> str:
        return ", ".join(self.names)


# ----------------------------- AppCreator ----------------------------- #


class AppCreator:
    """Generates Flask routes, TypeScript request wrappers, and schemas."""

    APP_IMPORTS = [
        'from flask import Flask, request, jsonify, Response',
        'from flask_cors import CORS',
        'from AppConfig import AppConfig',
        'from objects import *',
        'from ApiRequests import ApiRequests',
        'import os',
        'import logging',
        'from appPubSub import main',
        'from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)',
        'from Settings import DatabaseSettingUpdater',
        'from datetime import timedelta',
        'import traceback',
    ]

    APP_PUBSUB_IMPORTS = [
        'from flask import Blueprint, jsonify, request',
        'import logging',
        'from mongoDb import mongoDb',
        'from PubSubRequests import PubSubRequests',
        'import traceback',
        'from pubSub import PubSub'
    ]

    APP_FLASK_CONFIG = [
        'app = Flask(__name__)',
        'app.register_blueprint(main)',
        'if os.getenv("JWT_SECRET_KEY") == None:',
        '    raise ValueError("JWT_SECRET_KEY environment variable is not set")',
        'app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")',
        'app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)',
        'jwt = JWTManager(app)',
        'CORS(app, resources={r"/*": {"origins": "*"}})',
        'logging.basicConfig(level=logging.INFO)',
    ]

    APP_PUBSUB_CONFIG = [
        "main = Blueprint('main', __name__)",
        'logging.basicConfig(level=logging.INFO)',
    ]

    def __init__(self, apiRequests: ApiRequests):
        self.apiRequests = apiRequests
        # use global constant
        self.objectsPath = str(OBJECTS_PY_PATH)

    # ----------------------------- Path helpers ----------------------------- #
    def _project_root(self) -> str:
        root = os.path.dirname(os.path.abspath(__file__))
        while not os.path.exists(os.path.join(
                root, '.git')) and os.path.dirname(root) != root:
            root = os.path.dirname(root)
        return root

    # ----------------------------- Introspection helpers ----------------------------- #
    def _get_user_defined_methods(self, kind: str):
        requestClass = ApiRequests if kind == 'app' else PubSubRequests
        methods = {}
        for cls in requestClass.__mro__:
            for name, func in cls.__dict__.items():
                if callable(func) and not name.startswith('_'):
                    methods.setdefault(name, func)
        return methods

    def _route_meta(self, func) -> Dict[str, Any]:
        return {
            'httpMethod': getattr(func, 'httpMethod', None),
            'jwtRequired': getattr(func, 'jwtRequired', None),
            'createAccessToken': getattr(func, 'createAccessToken', None),
            'successMessage': getattr(func, 'successMessage', None),
        }

    def _validate_route_meta(self, name: str, meta: Dict[str, Any],
                             fileName: str):
        if meta['httpMethod'] not in [
                'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'
        ]:
            raise ValueError(
                f"please set the http method of {name} in {fileName} file")
        if meta['jwtRequired'] not in [True, False]:
            raise ValueError(f"please set the jwtRequired in {fileName} file")
        if meta['createAccessToken'] not in [True, False]:
            raise ValueError(
                f"please set the createAccessToken in {fileName} file")

    # ----------------------------- Parameter helpers ----------------------------- #
    def _parameters(self, func: Callable) -> Parameters:
        names = [p for p in inspect.signature(func).parameters if p != 'self']
        return Parameters(names=names)

    def _params_with_annotations(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        result: Dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if name == 'self':
                continue
            ann = param.annotation
            if ann is inspect._empty:
                raise ValueError(
                    f"Function {func.__name__} parameter '{name}' missing type annotation"
                )
            origin = get_origin(ann)
            if origin in (typing.Union, types.UnionType):
                result[name] = ann
            else:
                result[name] = ann
        return result

    # ----------------------------- Flask generation ----------------------------- #
    def _imports(self, kind: str) -> str:
        imports = self.APP_IMPORTS if kind == 'app' else self.APP_PUBSUB_IMPORTS
        return "\n".join(imports) + "\n\n"

    def _flask_config(self, kind: str) -> str:
        cfg = self.APP_FLASK_CONFIG if kind == 'app' else self.APP_PUBSUB_CONFIG
        return "\n".join(cfg) + "\n\n"

    def _main_function_block(self, kind: str) -> str:
        if kind != 'app':
            return ''
        return ("""
if __name__ == '__main__':
    if (AppConfig().getIsDevEnvironment()):
        print(f"\033[92m_______________________{AppConfig().getEnvironment().upper()}_______________________\033[0m")
    if AppConfig().getIsProductionEnvironment():
        print(f"\033[91m_______________________{AppConfig().getEnvironment().upper()}_______________________\033[0m")

    from Settings import DatabaseSettingUpdater
    DatabaseSettingUpdater().updateDatabaseSettingsToDefault()

    if AppConfig().getisLocalEnvironment():
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        app.run(host='0.0.0.0', port=8080)
""")

    def _function_code(self, name: str, params: Parameters,
                       meta: Dict[str, Any], kind: str,method:str) -> str:
        atFunction = 'app' if kind == 'app' else 'main'
        className = 'ApiRequests' if kind == 'app' else 'PubSubRequests'

        parameters_check = '    if request.is_json:\n        data = request.get_json()\n' if method == 'POST' else ''
        parameters_code = params.as_assignment_block(indent=8)
        decode_message = '        data = message["data"]\n        message = data["message"]\n        data = PubSub().decodeMessage(data)\n' if kind == 'appPubSub' else ''
        jwt_decorator = '@jwt_required()' if meta['jwtRequired'] else ''
        current_user_code = '        current_user = get_jwt_identity()\n' if (
            meta['jwtRequired'] and not meta['createAccessToken']) else ''
        if not params.names:
            current_user_code = current_user_code.replace(
                '        ', '    ', 1)

        access_token_code = '        access_token = create_access_token(identity=res["_id"])\n' if meta[
            'createAccessToken'] else ''

        # Response code
        if meta['createAccessToken']:
            response_code = f'    return jsonify({{"message": "{meta["successMessage"]}","data":res,"status":200, "access_token": access_token}}), 200'
        elif meta['jwtRequired']:
            response_code = f'    return jsonify({{"message": "{meta["successMessage"]}","status":200, "current_user": current_user, "data": res}}), 200'
        else:
            response_code = f'    return jsonify({{"message": "{meta["successMessage"]}", "status":200, "data": res}}), 200'

        body_call = f"{className}().{name}({params.comma_join()})" if params.names else f"{className}().{name}(data)"

        return f"""
@{atFunction}.route('/{name}', methods=['{meta['httpMethod']}'])
{jwt_decorator}
def {name}():
{parameters_check}{parameters_code}{decode_message}{current_user_code}    try:
        res = {body_call}
{access_token_code}    except Exception as e:
        traceback.print_exc()
        return jsonify({{'message': str(e),'data':None,'status':400}}), 400

{response_code}\n"""

    def _all_functions_code(self, kind: str) -> str:
        out: List[str] = []
        for name, func in self._get_user_defined_methods(kind).items():
            meta = self._route_meta(func)
            fileName = 'ApiRequests' if kind == 'app' else 'PubSubRequests'
            self._validate_route_meta(name, meta, fileName)
            params = self._parameters(func)
            out.append(self._function_code(name, params, meta, kind,func.httpMethod))
        return "\n".join(out)

    # ----------------------------- TS generation ----------------------------- #
    def _ts_schema_imports(self, already: List[str]) -> str:
        schema_dir = str(CLIENT_SCHEMAS_DIR)
        import_lines: List[str] = []
        for file in os.listdir(schema_dir):
            if not file.endswith('.ts'):
                continue
            with open(os.path.join(schema_dir, file), 'r') as f:
                src = f.read()
            names = re.findall(
                r'export\s+(?:type|interface)\s+([A-Za-z0-9_]+)', src)
            unique: List[str] = []
            for n in names:
                if n not in already:
                    already.append(n)
                    unique.append(n)
            if unique:
                import_lines.append(
                    f"import type {{ {', '.join(unique)} }} from '../schemas/{file}';"
                )
        return "\n".join(import_lines)

    def _ts_method_code(self, name: str, params: Dict[str, Any],
                        meta: Dict[str, Any]) -> str:
        # Build param list
        param_list = ", ".join(f"{p}: {py_annotation_to_ts(a)}"
                               for p, a in params.items())
        body_keys = ", ".join(f'"{k}": {k}' for k in params.keys())

        auth_header = 'Authorization: `Bearer ${localStorage.getItem("access_token")}`' if meta[
            'jwtRequired'] else ''
        token_store = 'localStorage.setItem("access_token", data.access_token)' if meta[
            'createAccessToken'] else ''
        data_body = f"body: JSON.stringify({{{body_keys}}})," if meta[
            'httpMethod'] == 'POST' else ''

        return f"""
    async {name}({param_list}): Promise<any> {{
        try {{
        const res = await fetch(`${{this.apiUrl}}/{name}`, {{
            method: '{meta['httpMethod']}',
            headers: {{
            "Content-Type": "application/json",
            {auth_header}
            }},
            {data_body}
            cache: 'no-store'
        }});
        const data = await res.json();
        {token_store}
        return data;
        }} catch (error) {{
            console.error("Error:", error);
            return {{"message": "Failed to fetch data", "error": error}};
        }}
    }}"""

    def generateTSFile(self):  # kept name for backward compatibility
        already: List[str] = []
        methods = self._get_user_defined_methods('app')
        schema_imports = self._ts_schema_imports(already)

        ts_class_lines = [
            "/* eslint-disable @typescript-eslint/no-explicit-any */",
            "import Server from \"./Server\";", schema_imports, '',
            '    class ServerRequests extends Server {', '    constructor() {',
            '        super();', '    }', ''
        ]

        for name, func in methods.items():
            meta = self._route_meta(func)
            self._validate_route_meta(name, meta, 'ApiRequests')
            params = self._params_with_annotations(func)
            ts_class_lines.append(self._ts_method_code(name, params, meta))

        ts_class_lines.append("}")
        ts_class_lines.append("\nexport default ServerRequests;\n")

        serverCode = """
class Server {
    public apiUrl: string | null;
    constructor() {
        const next_env = process.env.NODE_ENV || 'development';
        const urls = { localApi: 'http://127.0.0.1:5000', productionApi: null };
        this.apiUrl = next_env === 'production' ? urls.productionApi : urls.localApi;
    }
}
export default Server;"""

        clientDir = str(CLIENT_API_DIR)
        os.makedirs(clientDir, exist_ok=True)
        with open(os.path.join(clientDir, 'Server.ts'), 'w') as f:
            f.write(serverCode)
        with open(os.path.join(clientDir, 'ServerRequests.ts'), 'w') as f:
            f.write("\n".join(ts_class_lines))
        print("Server.ts and ServerRequests.ts generated successfully!")

    # ----------------------------- Schema generation ----------------------------- #
    def _load_module(self, path: str, name: str | None = None):
        name = name or Path(path).stem
        spec = inspect.util.spec_from_file_location(
            name, path)  # type: ignore[attr-defined]
        if spec is None or spec.loader is None:  # defensive
            raise RuntimeError(f"Cannot load module from {path}")
        module = inspect.util.module_from_spec(
            spec)  # type: ignore[attr-defined]
        spec.loader.exec_module(module)  # type: ignore[assignment]
        return module

    def _classes_from_module(self, module):
        return [
            cls for _, cls in inspect.getmembers(module, inspect.isclass)
            if cls.__module__ == module.__name__
        ]

    def generateTypeScriptSchemas(self):
        # dynamic import of objects.py
        spec = importlib.util.spec_from_file_location('objects_mod',
                                                      self.objectsPath)
        module = importlib.util.module_from_spec(
            spec)  # type: ignore[arg-type]
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        classes = [
            cls for _, cls in inspect.getmembers(module, inspect.isclass)
            if cls.__module__ == module.__name__
        ]

        input_dir = str(SERVER_SCHEMAS_DIR)
        output_dir = str(CLIENT_SCHEMAS_DIR)
        os.makedirs(output_dir, exist_ok=True)

        for cls in classes:
            schema = cls.model_json_schema()
            schema['additionalProperties'] = False
            write_path = os.path.join(input_dir, f'{cls.__name__}Schema.json')
            with open(write_path, 'w') as jf:
                json.dump(schema, jf, indent=4)

        for filename in [
                f for f in os.listdir(input_dir) if f.endswith('.json')
        ]:
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.ts'
            output_path = os.path.join(output_dir, output_filename)
            command = f'json2ts -i "{input_path}" -o "{output_path}"'
            os.system(command)
            print(f"Generated TypeScript type for {filename} at {output_path}")

    # ----------------------------- Flask app generation ----------------------------- #
    def generateAPI(self, kind: str = 'app'):
        if kind not in {'app', 'appPubSub'}:
            raise ValueError('Type must be either "app" or "appPubSub"')
        code = self._imports(kind) + self._flask_config(
            kind) + self._all_functions_code(kind) + self._main_function_block(
                kind)
        target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   f'{kind}.py')
        with open(target_path, 'w') as f:
            f.write(code)
        print(f"Generated {kind}.py")


# ----------------------------- CLI Entry ----------------------------- #
if __name__ == '__main__':
    creator = AppCreator(apiRequests=ApiRequests())
    creator.generateTypeScriptSchemas()
    creator.generateTSFile()
    creator.generateAPI('app')
    creator.generateAPI('appPubSub')
