import os
import ast
from typing import List, Set, Optional
from mongoDb import pubSubMockDb
from AppConfig import Project


def test_ifAllApiRequestTested():
    """
    Test to ensure that all pubsub functions are tested.
    """
    # current_file_directory = 
    cwd = os.path.dirname(os.path.abspath(__file__))
    pubSubRequestsDirectory = cwd + '\\PubSubRequests.py'
    apiRequestsDirectory = cwd + '\\ApiRequests.py'
    print("pubSubRequestsDirectory: ", pubSubRequestsDirectory)

    def list_functions(filename: str) -> List[str]:
        """
        Parses the given Python file and returns a list of all class method names
        (excluding private and inner functions).
        """
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename)
        func_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item,
                                  (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not item.name.startswith('_'):
                            func_names.append(item.name)
        return func_names

    def list_called_or_referenced_functions(filename: str) -> List[str]:
        with open(filename, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename)
        called: Set[str] = set()

        def get_full_name(node):
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                parent = get_full_name(node.value)
                return f"{parent}.{node.attr}" if parent else node.attr
            else:
                return None

        class CallCollector(ast.NodeVisitor):
            def __init__(self):
                self.inside_pytest_raises = 0

            def visit_With(self, node):
                # Check if this is a 'with pytest.raises(...)' block
                for item in node.items:
                    ctx_expr = item.context_expr
                    if (isinstance(ctx_expr, ast.Call) and
                        isinstance(ctx_expr.func, ast.Attribute) and
                        ctx_expr.func.value.id == 'pytest' and
                        ctx_expr.func.attr == 'raises'):
                        self.inside_pytest_raises += 1
                        for n in node.body:
                            self.visit(n)
                        self.inside_pytest_raises -= 1
                        break
                else:
                    self.generic_visit(node)

            def visit_Call(self, node):
                if self.inside_pytest_raises == 0:
                    name = get_full_name(node.func)
                    if name:
                        called.add(name)
                self.generic_visit(node)

            def visit_Attribute(self, node):
                # Only add if not inside pytest.raises
                if self.inside_pytest_raises == 0:
                    parent = getattr(node, 'ctx', None)
                    if isinstance(parent, ast.Load):
                        name = get_full_name(node)
                        if name:
                            called.add(name)
                self.generic_visit(node)

        CallCollector().visit(tree)
        return sorted(called)

    # Read the file and check for pubsub functions
    pubSubFunctions = list_functions(pubSubRequestsDirectory)
    appFunctions = list_functions(apiRequestsDirectory)

    #get server directory
    serverDirectory = cwd
    #read all files in server directory
    serverFiles = os.listdir(serverDirectory)

    allTestFunctions = []
    for x in serverFiles:
        if x.startswith('test_') and x.endswith('.py'):
            testFile = serverDirectory + '\\' + x
            print("testFile: ", testFile)
            # Read the file and check for pubsub functions
            testFunctions = list_called_or_referenced_functions(testFile)
            print("Test functions found in", x, ":", testFunctions)

            for y in testFunctions:
                allTestFunctions.append(y)

    for x in pubSubFunctions:
        if x not in allTestFunctions:
            raise Exception(
                f"PubSub function '{x}' is not tested in any test file. Please add a test for it."
            )

    for x in appFunctions:
        if x not in allTestFunctions:
            raise Exception(
                f"App function '{x}' is not tested in any test file. Please add a test for it."
            )

    
    allCollections = pubSubMockDb.getAllCollections()
    
    if len(allCollections) == 0:
        raise Exception("No collections found in pubSubMockDb. Please add mock data to the database.")

    allMockDataMessages = []
    for collection in allCollections:
        allCollectionMockData = pubSubMockDb.read({},collection)
        for data in allCollectionMockData:
            if Project().projectName in data['projectNameConsumers']:
                allMockDataMessages.append(data)
    allMockDataFunctions = set([x['consumeFunctionName'] for x in allMockDataMessages])

    for x in allMockDataFunctions:
        if x not in pubSubFunctions:
            raise Exception(
                f"PubSub function '{x}' is not in PubSubRequests.py Please add the function to receive this message."
            )


if __name__ == "__main__":
    test_ifAllApiRequestTested()
