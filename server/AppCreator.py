from pydantic2ts import generate_typescript_defs
from typing import Union, List
from ApiRequests import ApiRequests
from PubSubRequests import PubSubRequests
import os
import inspect
import subprocess
import json
import importlib.util
import sys
from pathlib import Path
import types
from typing import Any, Dict, Union, Callable, get_origin, get_args
import re
import datetime
import inspect
import typing
from typing import Any


def py_annotation_to_ts(ann: Any) -> str:
    """
    Convert any Python type annotation to a TypeScript type string.
    """
    # No annotation -> any
    if ann is inspect._empty:
        return "any"
    # NoneType -> null
    if ann is type(None):
        return "null"

    # Map basic Python types to TS primitives
    PY_TO_TS = {
        int: "number",
        float: "number",
        str: "string",
        bool: "boolean",
        dict: "Object",
        list: "any[]",
        Any: "any",
        None: "null",
        datetime.datetime: "Date",
    }
    if isinstance(ann, type) and ann in PY_TO_TS:
        return PY_TO_TS[ann]
    if ann in PY_TO_TS:
        return PY_TO_TS[ann]

    # Handle typing constructs
    origin = typing.get_origin(ann)
    args = typing.get_args(ann) or ()

    # List[T] -> T[]
    if origin in (list, typing.List):
        item_type = py_annotation_to_ts(args[0]) if args else "any"
        return f"{item_type}[]"

    # Dict[K, V] -> Record<K, V>
    if origin in (dict, typing.Dict):
        if len(args) == 2:
            key_ts = py_annotation_to_ts(args[0])
            val_ts = py_annotation_to_ts(args[1])
            return f"Record<{key_ts}, {val_ts}>"
        return "Record<string, any>"

    # Tuple[T1, T2, ...] -> [T1, T2, ...]
    # Tuple[T, ...]     -> T[]
    if origin in (tuple, typing.Tuple):
        if not args:
            return "any[]"
        # homogeneous tuple: Tuple[T, ...]
        if len(args) == 2 and args[1] is Ellipsis:
            return f"{py_annotation_to_ts(args[0])}[]"
        # fixed-length tuple: Tuple[T1, T2, ...]
        ts_elems = ", ".join(py_annotation_to_ts(a) for a in args)
        return f"[{ts_elems}]"

    # Union[...] -> A | B | C
    if origin is typing.Union:
        ts_parts = [py_annotation_to_ts(a) for a in args]
        return " | ".join(ts_parts)

    # Optional[T] is Union[T, NoneType]
    # (this is actually covered by the Union case, but you can specialize if you like)
    if origin is typing.Optional:
        return f"{py_annotation_to_ts(args[0])} | null"

    # Forward references or bare strings
    if isinstance(ann, str):
        return ann

    # Fallback: use the annotation's __name__
    try:
        return ann.__name__
    except AttributeError:
        if type(ann) is tuple:
            # Handle typing.Union as a tuple
            ts_parts = [py_annotation_to_ts(a) for a in ann]
            return " | ".join(ts_parts)


# Example usage
examples = [
    (int, "number"),
    (str, "string"),
    (None, "any"),  # inspect._empty example
    (typing.List[int], "number[]"),
    (typing.Dict[str, int], "Record<string, number>"),
    (typing.Union[str, None], "string | null"),
    ("CustomType", "CustomType"),
    (typing.Optional[bool], "boolean | null"),
]

print("Python annotation -> TypeScript type")
for ann, expected in examples:
    # For None example, use inspect._empty
    ann_to_test = ann if ann is not None else inspect._empty
    print(f"{ann_to_test!r:30} -> {py_annotation_to_ts(ann_to_test)}")


class ParametersAndAnnotationsDict():

    def __init__(self, data):
        self.data = data

    def generateParametersWithAnnotations(self):
        """
#         Return each parameter as an assignment line,
#         indented to match the code block under 'data = request.get_json()'.
#         """
        # Adjust this indentation to match your desired code layout.
        # In this example, we use 16 spaces so that it lines up with
        # a code block that is already indented in a triple-quoted string.
        indentation = " " * 8
        lines = []
        for x in self.data:
            lines.append(f"{indentation}{x} = data['{x}']")
        # Join the lines with a newline, then add a trailing newline
        return "\n".join(lines) + "\n"


class Parameters():

    def __init__(self, parameters: List[str]):
        self.parameters = parameters

    def getParameters(self):
        return self.parameters

    def getParametersAsCode(self):
        """
        Return each parameter as an assignment line,
        indented to match the code block under 'data = request.get_json()'.
        """
        # Adjust this indentation to match your desired code layout.
        # In this example, we use 16 spaces so that it lines up with
        # a code block that is already indented in a triple-quoted string.
        indentation = " " * 8
        lines = []
        for x in self.parameters:
            lines.append(f"{indentation}{x} = data['{x}']")
        # Join the lines with a newline, then add a trailing newline
        return "\n".join(lines) + "\n"


#     def __init__(self, parameters: List[str]):
#         self.parameters = parameters

#     def getParameters(self):
#         return self.parameters

#     def getParametersAsCode(self):
#         """
#         Return each parameter as an assignment line,
#         indented to match the code block under 'data = request.get_json()'.
#         """
#         # Adjust this indentation to match your desired code layout.
#         # In this example, we use 16 spaces so that it lines up with
#         # a code block that is already indented in a triple-quoted string.
#         indentation = " " * 8
#         lines = []
#         for x in self.parameters:
#             lines.append(f"{indentation}{x} = data['{x}']")
#         # Join the lines with a newline, then add a trailing newline
#         return "\n".join(lines) + "\n"


class AppCreator():

    def __init__(self, apiRequests: ApiRequests):
        # model_config = ConfigDict(arbitrary_types_allowed=True)
        self.apiRequests = apiRequests
        self.appImports: list[str] = [
            'from flask import Flask, request, jsonify, Response',
            'from flask_cors import CORS', 'from AppConfig import AppConfig',
            'from objects import *', 'from ApiRequests import ApiRequests',
            'import os', 'import logging', 'from appPubSub import main',
            'from flask_jwt_extended import (JWTManager, create_access_token, jwt_required, get_jwt_identity)',
            'from Settings import DatabaseSettingUpdater',
            "from datetime import timedelta", 'import traceback'
        ]
        self.appPubsubImports: list[str] = [
            'from flask import Blueprint, jsonify, request', 'import logging',
            'from mongoDb import mongoDb',
            'from PubSubRequests import PubSubRequests', 'import traceback'
        ]
        self.appFlaskConfig: list[str] = [
            'app = Flask(__name__)',
            'app.register_blueprint(main)',
            'if os.getenv("JWT_SECRET_KEY") == None:',
            '    raise ValueError("JWT_SECRET_KEY environment variable is not set")',
            'app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")',
            'app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)',
            'jwt = JWTManager(app)',
            '',
            '',
            """CORS(app, resources={r"/*": {"origins": "*"}})""",
            'logging.basicConfig(level=logging.INFO)',
        ]
        self.appPubSubConfig: list[str] = [
            "main = Blueprint('main', __name__)",
            'logging.basicConfig(level=logging.INFO)'
        ]
        # INPUT OBJECTS PATH HERE
        pathOfCurrentFile = os.path.abspath(__file__)
        current_directory = os.path.dirname(pathOfCurrentFile)
        self.objectsPath = current_directory + "\\objects.py"

    def __getProjectRootDir(self):
        projectRoot = os.path.dirname(os.path.abspath(__file__))

        while not os.path.exists(os.path.join(
                projectRoot,
                '.git')) and os.path.dirname(projectRoot) != projectRoot:
            projectRoot = os.path.dirname(projectRoot)

        return projectRoot

    def __getAppCreatorDir(self):
        filePath = os.path.abspath(__file__)
        fileDirectory = os.path.dirname(filePath)

        return fileDirectory

    def __generateFunctionCode(self, methodName: str, parameters: Parameters,
                               httpMethod: str, jwtRequired: bool,
                               createAccessToken: bool, successMessage: str,
                               type: str) -> str:

        if type == 'app':
            atFunction = 'app'
            className = 'ApiRequests'
        elif type == 'appPubSub':
            atFunction = 'main'
            className = 'PubSubRequests'

        parameters_code = parameters.getParametersAsCode()
        parameters_check = '    if request.is_json: \n        data = request.get_json()\n' if parameters.getParameters(
        ) else ''

        jwt_decorator = '@jwt_required()' if jwtRequired else ''
        current_user_code = '        current_user = get_jwt_identity()\n' if not createAccessToken and jwtRequired is True else ''
        access_token_code = '        access_token = create_access_token(identity=res["_id"])\n' if createAccessToken else ''

        if not parameters.getParameters():
            current_user_code = current_user_code.replace(
                '        ', '    ', 1)

        response_code = (
            f'    return jsonify({{"message": "{successMessage}","data":res,"status":200, "access_token": access_token}}), 200'
            if createAccessToken else
            f'    return jsonify({{"message": "{successMessage}","status":200, "current_user": current_user, "data": res}}), 200'
            if httpMethod
            in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
            and jwtRequired else
            f'    return jsonify({{"message": "{successMessage}", "status":200, "data": res}}), 200'
        )

        # Generate the function code
        code = f"""
@{atFunction}.route('/{methodName}', methods=['{httpMethod}'])
{jwt_decorator}
def {methodName}():
{parameters_check}
{parameters_code}
{current_user_code}
    try:
        res = {className}().{methodName}({", ".join(parameters.getParameters())})
{access_token_code}
    except Exception as e:
        traceback.print_exc()
        return jsonify({{'message': str(e),'data':None,'status':400}}), 400

{response_code}
    \n\n"""

        return code

    def __route_config(self, func, type):
        name = func.__name__
        httpMethod = getattr(func, 'httpMethod', None)
        jwtRequired = getattr(func, 'jwtRequired', None)
        createAccessToken = getattr(func, 'createAccessToken', None)
        successMessage = getattr(func, 'successMessage', None)

        if type == 'app':
            fileName = 'ApiRequests'
        elif type == 'appPubSub':
            fileName = 'PubSubRequests'

        print(httpMethod, jwtRequired, createAccessToken, successMessage)

        if httpMethod not in [
                'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'
        ]:
            raise ValueError(
                f'please set the http method of {name} in {fileName} file')
        if jwtRequired not in [True, False]:
            raise ValueError(f'please set the jwtRequired in {fileName} file')
        if createAccessToken not in [True, False]:
            raise ValueError(
                f'please set the createAccessToken in {fileName} file')

        return {
            'httpMethod': httpMethod,
            'jwtRequired': jwtRequired,
            'createAccessToken': createAccessToken,
            'successMessage': successMessage
        }

    def __getParameters(self, func: callable) -> Parameters:
        return Parameters(parameters=[
            p for p in inspect.signature(func).parameters if p != "self"
        ])

    def __generateAllFunctionCode(self, type):
        userDefinedMethods = self.__getUserDefinedMethods(type)
        functionCodes = ""
        print(userDefinedMethods.items().__getattribute__)
        for name, func in userDefinedMethods.items():

            decorator = self.__route_config(func, type)
            parameters = self.__getParameters(func)
            functionCode = self.__generateFunctionCode(
                name, parameters, decorator['httpMethod'],
                decorator['jwtRequired'], decorator['createAccessToken'],
                decorator['successMessage'], type)
            functionCodes += functionCode

        return functionCodes

    def __generateImports(self, type: str):

        if type == 'app':
            imports = self.appImports
        elif type == 'appPubSub':
            imports = self.appPubsubImports

        importString = ''
        for x in imports:
            importString += x + '\n'

        return importString + '\n'

    def __generateFlaskConfig(self, type: str):

        if type == 'app':
            flaskConfig = self.appFlaskConfig
        elif type == 'appPubSub':
            flaskConfig = self.appPubSubConfig

        flaskConfigString = ''
        for x in flaskConfig:
            flaskConfigString += x + '\n'

        return flaskConfigString + '\n'

    def __generateMainFunction(self, type: str):
        if type == 'appPubSub':
            return ''

        return """ 
if __name__ == '__main__':
    if (AppConfig().getIsDevEnvironment()):
        print(
            f"\033[92m_______________________{AppConfig().getEnvironment().upper()}_______________________\033[0m"
        )
    if AppConfig().getIsProductionEnvironment():
        print(
            f"\033[91m_______________________{AppConfig().getEnvironment().upper()}_______________________\033[0m"
        )

    DatabaseSettingUpdater().updateDatabaseSettingsToDefault()

    if AppConfig().getisLocalEnvironment():
        # dev
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        # production
        app.run(host='0.0.0.0', port=8080)
        """

    def __getUserDefinedMethods(self, type):

        #get the request class
        if type == 'app':
            requestClass = ApiRequests
        elif type == 'appPubSub':
            requestClass = PubSubRequests

        # Get all methods from ApiRequests and its parent classes (including inherited ones)
        user_defined_methods = {}

        # Iterate through the MRO (Method Resolution Order) of ApiRequests
        for cls in requestClass.__mro__:
            # Only consider methods that are callable and are not starting with an underscore
            for name, func in cls.__dict__.items():
                if callable(func) and not name.startswith("_"):
                    # Ensure we don't add the method multiple times (if it's inherited)
                    if name not in user_defined_methods:
                        user_defined_methods[name] = func

                        print(
                            f"Method: {name}, httpMethod: {getattr(func, 'httpMethod', None)}, "
                            f"jwtRequired: {getattr(func, 'jwtRequired', None)}, "
                            f"createAccessToken: {getattr(func, 'createAccessToken', None)}, "
                            f"successMessage: {getattr(func, 'successMessage', None)}"
                        )

        return user_defined_methods

    def __getParametersAndAnnotations(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        params_with_annotations: Dict[str, Any] = {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            ann = param.annotation

            # 1) no annotation
            if ann is inspect._empty:
                params_with_annotations[name] = None
                continue

            # 2) unwrap X | Y (PEP 604) or Union[X, Y]
            origin = get_origin(ann)
            if origin is Union or origin is types.UnionType:
                # get_args gives you a tuple of the member types, e.g. (str, NoneType)
                params_with_annotations[name] = get_args(ann)
                continue

            # 3) plain classes, built-ins, etc.
            if hasattr(ann, "__name__"):
                params_with_annotations[name] = ann
                continue

            # 4) fallback: leave the annotation object as-is
            params_with_annotations[name] = ann

        return params_with_annotations

    def generateAPI(self, type: str = 'app'):

        if type not in ['app', 'appPubSub']:
            raise ValueError('Type must be either "app" or "appPubSub"')

        imports = self.__generateImports(type)
        flaskConfig = self.__generateFlaskConfig(type)
        functionCodes = self.__generateAllFunctionCode(type)
        mainFunction = self.__generateMainFunction(type)

        print(imports + flaskConfig + functionCodes + mainFunction)

        # create a app.py file and write the generated code to it
        AppCreatorDirectory = self.__getAppCreatorDir()

        print(f"App Creator Directory: {AppCreatorDirectory}")

        with open(AppCreatorDirectory + f'/{type}' + '.py', 'w') as f:
            f.write(imports + flaskConfig + functionCodes + mainFunction)

    def __check_if_union_str(self, value: str):
        if '|' in value:
            return True

    def __params_to_ts(self, parameters: Dict[str, Union[str, type,
                                                         None]]) -> str:
        """
        Convert param->annotation into a TS param list, handling:
        - 'str|None' → 'string | null'
        - typing.Union[X, Y]
        - typing.List[X]
        """

        parts = []
        for name, ann in parameters.items():
            if name == 'stickerServerEndpoint':
                print('test')
            ts_type = py_annotation_to_ts(ann)
            parts.append(f"{name}: {ts_type}")

        return ", ".join(parts)

    def __generateTSFunctionCode(self, methodName: str, parameters: dict,
                                 httpMethod: str, jwtRequired: bool,
                                 createAccessToken: bool) -> str:
        """ Generate TS function code for each method using axios """

        for key, value in parameters.items():
            if value == None:
                raise ValueError(
                    f"Function {methodName}, Parameter '{key}' has a value of None. Please provide a valid type annotation."
                )

        # Prepare TypeScript parameters with explicit types
        paramList = self.__params_to_ts(parameters)

        # Generate key-value pairs for the body
        keyValuePairs = ", ".join(
            [f'"{key}": {key}' for key, value in parameters.items()])

        authorization_check = 'Authorization: `Bearer ${localStorage.getItem("access_token")}`' if jwtRequired else ''
        token_store = 'localStorage.setItem("access_token", data.access_token)' if createAccessToken else ''
        headers = f"""headers: {{
            "Content-Type": "application/json",
            {authorization_check}
            }}"""

        dataBody = f"""body: JSON.stringify({{{keyValuePairs}}}),""" if httpMethod == 'POST' else ''

        # Fetch request with destructured body parameters
        # if jwtRequired:
        body = f"""
        const res = await fetch(`${{this.apiUrl}}/{methodName}`, {{
            method: '{httpMethod}',
            {headers},
            {dataBody}
            cache: 'no-store'
        }});
        const data = await res.json();
        {token_store}"""

        # else:
        #     body = f"""
        #     const res = await fetch(`${{this.apiUrl}}/{methodName}`, {{
        #         method: "{httpMethod}",
        #     }});
        #     const data = await res.json();"""

        # Generate the complete function code
        code = f"""
    async {methodName}({paramList}): Promise<any> {{
        try {{{body}
        return data;
        }} catch (error) {{
            console.error("Error:", error);
            return {{"message": "Failed to fetch data", "error": error}};
        }}
    }}\n"""

        return code

    def __generate_ts_import(self, source: str, module_path: str,
                             schemasGenerated: list) -> str:
        """
        Given the text of a TS file (with `export type` and `export interface` lines)
        and the desired module path, returns a string like:

        import type { A, B, C } from 'module_path';

        """
        # find all exported type & interface names
        names = re.findall(r'export\s+(?:type|interface)\s+([A-Za-z0-9_]+)',
                           source)

        # dedupe while preserving order
        seen = set()
        unique: List[str] = []
        for n in names:
            if n in schemasGenerated:
                continue
            elif n not in seen:
                seen.add(n)
                unique.append(n)
                schemasGenerated.append(n)

        # format into a single import line
        joined = ", ".join(unique)
        return f"import type {{ {joined} }} from '{module_path}';"

    def __getSchemaImports(self, schemasGenerated):
        cd = os.getcwd()
        schemaFolderDirectory = cd + '\\client\\src\\app\schemas'
        #get all folder names
        schemaFiles = os.listdir(schemaFolderDirectory)
        importStrings = []
        for x in schemaFiles:
            with open(schemaFolderDirectory + '\\' + x, "r") as f:
                ts_source = f.read()
            importString = self.__generate_ts_import(ts_source,
                                                     '../schemas/' + x,
                                                     schemasGenerated)
            importStrings.append(importString)

        return importStrings

    def generateTSFile(self):
        """ Generate the serverrequests.tsx file """

        schemasGenerated = []
        methods = self.__getUserDefinedMethods('app')
        allSchemaImports = self.__getSchemaImports(
            schemasGenerated)  # e.g. ["import type { User } from '...';", ...]

        # Join them into one string with real newlines
        allSchemaImportsString = "\n".join(allSchemaImports)

        # Generate imports and class definition
        tsCode = f"""/* eslint-disable @typescript-eslint/no-explicit-any */
import Server from "./Server";
{allSchemaImportsString}

    class ServerRequests extends Server {{
    constructor() {{
        super();
    }}

    """

        # Add methods dynamically
        for name, func in methods.items():
            decorator = self.__route_config(func, 'app')
            parametersAndAnnotation = self.__getParametersAndAnnotations(func)
            functionCode = self.__generateTSFunctionCode(
                name, parametersAndAnnotation, decorator['httpMethod'],
                decorator['jwtRequired'], decorator['createAccessToken'])
            tsCode += functionCode

        tsCode += """
}

export default ServerRequests;
        """

        serverCode = """

class Server {
    public apiUrl: string | null;

    constructor() {
        const next_env = process.env.NODE_ENV || 'development';
        const urls = {
            localApi: 'http://127.0.0.1:5000',
            productionApi: null,
        };

        this.apiUrl = next_env === 'production' ? urls.productionApi : urls.localApi;
    }
}

export default Server;"""

        projectRoot = self.__getProjectRootDir()

        print(f"Project root: {projectRoot}")

        clientDir = os.path.join(projectRoot, 'client\\deadletter\\app\\api')

        with open(os.path.join(clientDir, 'Server.ts'), 'w') as f:
            f.write(serverCode)

        # Write the file
        with open(os.path.join(clientDir, 'ServerRequests.ts'), 'w') as f:
            f.write(tsCode)

        print("Server.ts and ServerRequests.ts generated successfully!")

    def __load_module_from_path(self, path: str, name: str = None):
        name = name or Path(path).stem
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def __get_classes_from_module(self, module):
        return [
            cls for _, cls in inspect.getmembers(module, inspect.isclass)
            # only classes defined in that module
            if cls.__module__ == module.__name__
        ]

    def generateTypeScriptSchemas(self):
        mod = self.__load_module_from_path(self.objectsPath)
        classes = self.__get_classes_from_module(mod)

        input_dir = os.path.join(os.getcwd() + '\\Server\\schemas')
        output_dir = os.path.join(os.getcwd() + '\\client\\deadletter\\app\\schemas')

        for x in classes:
            className = x.__name__
            schema = x.model_json_schema()
            schema['additionalProperties'] = False
            writeDirectory = os.path.join(input_dir + '\\' + className +
                                          'Schema.json')
            with open(writeDirectory, 'w') as json_file:
                json.dump(schema, json_file, indent=4)

        # Set the directories for input JSON files and output TypeScript files

        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        inputFileNames = os.listdir(input_dir)

        #if file name is not json remove from list
        for fileName in inputFileNames:
            if not fileName.endswith('.json'):
                inputFileNames.remove(fileName)

        # Iterate over each JSON file in the input directory
        for filename in inputFileNames:
            input_path = os.path.join(input_dir, filename)
            output_filename = os.path.splitext(filename)[0] + '.ts'
            output_path = os.path.join(output_dir, output_filename)

            # Run the json-schema-to-typescript command
            command = f'json2ts -i "{input_path}" -o "{output_path}"'
            try:
                os.system(command)
                print(
                    f"Generated TypeScript type for {filename} at {output_path}"
                )
            except subprocess.CalledProcessError as e:
                print(f"Error generating TypeScript for {filename}: {e}")


if __name__ == '__main__':
    AppCreator(apiRequests=ApiRequests()).generateTypeScriptSchemas()
    AppCreator(apiRequests=ApiRequests()).generateTSFile()
    AppCreator(apiRequests=ApiRequests()).generateAPI('app')
    AppCreator(apiRequests=ApiRequests()).generateAPI('appPubSub')
