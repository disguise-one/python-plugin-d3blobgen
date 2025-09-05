import ast
import inspect
import functools
import requests
import textwrap
import json
from pydantic import BaseModel, Field
from typing import TypeVar, ParamSpec, Callable, Any, Generic, DefaultDict
from collections import defaultdict


class FunctionInfo(BaseModel):
    """Container for parsed function information extracted from Python source code.
    
    This model holds all the essential components of a function after parsing,
    including its complete definition, name, body statements, and argument list.
    """
    blob: str = Field(description="full body of function blob without decorator (Function definition + body)")
    blob_py27: str =  Field(description="full body of function blob without decorator in python2.7 format (Function definition + body)")
    name: str = Field(description="name of extracted function")
    body: str = Field(description="body of extracted function in str format")
    body_py27: str = Field(description="body of extracted function in python2.7 str format")
    args: list[str] = Field(default=[], description="list of arguments from extracted function")

def convert_ann_assign_to_assign(ann_assign_node: ast.AnnAssign) -> ast.Assign|None:
    """Convert an annotated assignment node to a regular assignment node.
    
    This function transforms type-annotated variable assignments (e.g., 'x: int = 5') 
    into regular assignments (e.g., 'x = 5') for Python 2.7 compatibility.
    
    Args:
        ann_assign_node: AST node representing an annotated assignment.
        
    Returns:
        ast.Assign node without type annotation, or None if no value is assigned.
    """
    if ann_assign_node.value is None:
        return None
    
    return ast.Assign(
        targets=[ann_assign_node.target],
        value=ann_assign_node.value,
        lineno = ann_assign_node.lineno,
        col_offset = ann_assign_node.col_offset)

class FastRemoveTypeHints(ast.NodeTransformer):
    """AST transformer to remove type hints from Python code for 2.7 compatibility."""
    
    def visit_AnnAssign(self, node):
        """Transform annotated assignment nodes to regular assignment nodes.
        
        Args:
            node: The annotated assignment AST node to transform.
            
        Returns:
            Regular assignment node without type annotation.
        """
        return convert_ann_assign_to_assign(node)

def remove_type_hints_from_body(function_node: ast.FunctionDef) -> None:
    """Remove type hints from the body statements of a function.
    
    This function applies the FastRemoveTypeHints transformer to remove
    annotated assignments from function body statements.
    
    Args:
        function_node: The function AST node to process.
    """
    transformer = FastRemoveTypeHints()
    transformer.visit(function_node)

def convert_to_py27(function_node: ast.FunctionDef) -> None:
    """Convert a function AST node to Python 2.7 compatible format.
    
    This function removes all type annotations from a function definition,
    including return type annotations, parameter type annotations, and
    type hints within the function body to ensure Python 2.7 compatibility.
    
    Args:
        function_node: The function AST node to convert to Python 2.7 format.
    """
    # Strip type hints for Python 2 compatibility
    # Remove return type annotation
    function_node.returns = None
    
    # Remove argument type annotations
    for arg in function_node.args.args:
        arg.annotation = None
    
    # Remove keyword-only argument type annotations
    for arg in function_node.args.kwonlyargs:
        arg.annotation = None
    
    # Remove vararg type annotation (*args)
    if function_node.args.vararg:
        function_node.args.vararg.annotation = None
    
    # Remove kwarg type annotation (**kwargs)  
    if function_node.args.kwarg:
        function_node.args.kwarg.annotation = None
    
    # Remove type hints from function body
    remove_type_hints_from_body(function_node)

def extract_function_info(func: Callable[..., Any]) -> FunctionInfo:
    """Parse function source code and extract name, body statements, and argument list.
    
    This function uses AST parsing to extract function information from the source code
    of a callable Python function. It removes decorators and provides the clean function
    definition along with parsed components.
    
    Args:
        func: A callable Python function to analyse.
        
    Returns:
        FunctionInfo: Object containing function name, body code, and argument names.
        
    Raises:
        ValueError: If the input is not a function or cannot be parsed.
    """
    
    source_code = inspect.getsource(func)
    # Remove common leading whitespace to handle functions defined with indentation
    source_code = textwrap.dedent(source_code)
    tree: ast.Module = ast.parse(source_code)
    
    # Check if first node exists and is a function
    if not tree.body:
        raise ValueError(f"Given input is not a function\ninput:{source_code}")
    
    first_node = tree.body[0]
    if not isinstance(first_node, ast.FunctionDef):
        raise ValueError(f"Given input is not a function\ninput:{source_code}")
    
    # Extract function blob without decorator
    first_node.decorator_list.clear()
    
    # Extract blob in python 3 format
    blob:str = ast.unparse(first_node)

    # Extract function name
    function_name = first_node.name

    # Extract body statements
    body_nodes = first_node.body
    
    # Convert back to source code
    body = ""
    for stmt in body_nodes:
        body += ast.unparse(stmt) + "\n"

    # Extract function arguments
    args: list[str] = []
    for arg in first_node.args.args:
        args.append(arg.arg)
        arg.type_comment
    
    convert_to_py27(first_node)
    blob_py27:str = ast.unparse(first_node)

    body_py27 = ""
    for stmt in body_nodes:
        body_py27 += ast.unparse(stmt) + "\n"

    return FunctionInfo(
        blob=blob,
        blob_py27=blob_py27,
        name=function_name,
        body=body.strip(),
        body_py27=body_py27,
        args=args
    )

P = ParamSpec('P')
T = TypeVar('T')
class D3Function(Generic[P, T]):
    """Wrapper class for Python functions to be executed in Designer environment.
    
    This class transforms regular Python functions into Designer plugin compatible functions
    that can be registered as modules and executed remotely. It preserves function metadata
    and provides methods for generating execution blobs and registration data.
    """

    _available_d3functions: DefaultDict[str, set["D3Function"]] = defaultdict(set)
    _registered_ipaddr:str = "localhost"

    def __init__(self, module_name: str, func: Callable[P, T]):
        """Initialise a D3Function wrapper around a Python function.
        
        Args:
            module_name: Name of the module to register this function under. 
                        Empty string means standalone function execution.
            func: The Python function to wrap for D3 execution.
        """
        self._module_name: str = module_name
        self._function: Callable[P, T] = func
        self._function_info: FunctionInfo = extract_function_info(func)
        self._is_module_function:bool = len(module_name) > 0
        
        # Update wrapper to preserve function metadata for IDE
        functools.update_wrapper(self, func)

        # Add this function into available_d3_functions
        D3Function._available_d3functions[module_name].add(self)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self._function(*args, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the original function for IDE support.
        
        Args:
            name: The attribute name to retrieve from the wrapped function.
            
        Returns:
            The attribute value from the wrapped function.
        """
        return getattr(self._function, name)
    
    def __hash__(self) -> int:
        """Used to uniquely register d3function in D3Function._available_d3functions. 
        Function name in python is unique, so we can function name as uid.
        
        Returns:
            Hash value of the function name.
        """
        return hash(self.name)
    
    def __eq__(self, other) -> bool:
        """Used to uniquely register d3function in D3Function._available_d3functions. 
        Function name in python is unique, so we can function name as uid.
        
        Returns:
            True if both are D3Functions with the same name, False otherwise.
        """
        if not isinstance(other, D3Function):
            return False
        return self.name == other.name

    @staticmethod
    def get_module_register_blob(module_name:str):
        """Generate a registration blob for all functions in a specific module.
        
        Args:
            module_name: The name of the module to generate the blob for.
            
        Returns:
            Dictionary containing module name and all d3function registered under module.
        """
        return {
            "moduleName": module_name,
            "contents": "\n\n".join([func.function_info.blob_py27 for func in D3Function._available_d3functions[module_name]])
        }

    @property 
    def __signature__(self) -> inspect.Signature:
        """Expose function signature for IDE introspection.
        
        Returns:
            The signature of the wrapped function for IDE support.
        """
        return inspect.signature(self._function)
    
    @property
    def name(self) -> str:
        """Get the name of the wrapped function.
        
        Returns:
            The name of the wrapped function.
        """
        return self.function_info.name

    @property
    def module_name(self) -> str:
        """Get the module name this function is registered under.
        
        Returns:
            The module name for this function.
        """
        return self._module_name

    @property
    def function_info(self) -> FunctionInfo:
        """Get the parsed function information.
        
        Returns:
            FunctionInfo object containing parsed details about the wrapped function.
        """
        return self._function_info

    def _args_to_string(self, *args, **kwargs) -> str:
        """Convert function arguments to a string representation for D3 script generation.
        
        Returns:
            String representation of all arguments suitable for function calls.
        """
        # Convert positional args
        args_parts = [repr(arg) for arg in args]
        # Convert keyword args  
        kwargs_parts = [f"{key}={repr(value)}" for key, value in kwargs.items()]
        # Combine them
        all_parts = args_parts + kwargs_parts
        return f"{', '.join(all_parts)}"

    def _args_to_assign(self, *args, **kwargs):
        """Convert function arguments to assignment statements for standalone execution.
        
        Returns:
            String containing variable assignment statements, one per line.
        """
        args_parts = [f"{self._function_info.args[i]}={repr(arg)}" for i, arg in enumerate(args)]
        kwargs_parts = [f"{name}={repr(value)}" for name, value in kwargs.items()]
        return "\n".join(args_parts + kwargs_parts)

    def get_execute_blob(self, *args: P.args, **kwargs: P.kwargs) -> dict[str, str]:
        """Generate an execution blob for running this function in Designer.
            
        Returns:
            - **module execute blob** if @d3function was registered with module_name
            - **script execute blob** if @d3function was registered without module_name
        """
        if self._is_module_function:
            return {
                "moduleName": self._module_name,
                "script": f"return {self._function_info.name}({self._args_to_string(*args, **kwargs)})"
            }
        else:
            all_args: str = self._args_to_assign(*args, **kwargs)
            return {
                "script": f"{all_args}\n{self._function_info.body_py27}"
            }
    
    def execute(self, *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute this function remotely on a D3 Designer instance.
        
        This method sends the function and its arguments to the registered Designer
        instance for remote execution, then returns the parsed result.
        
        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            The return value from the remote function execution.
            
        Raises:
            RuntimeError: If the HTTP request fails, Designer returns an error,
                         or the return value is empty/invalid.
        """
        response: requests.Response = requests.post(
            url=f"http://{D3Function._registered_ipaddr}/api/session/python/execute", 
            json=self.get_execute_blob(*args, **kwargs)
        )
        if not response.ok:
            raise RuntimeError(f"HTTP error {response.status_code}: { response.text}")
        
        data: dict = response.json()
        status: dict = data.get("status", {})
        if status.get("code") != 0:
            raise RuntimeError(f"""\
Designer API error:
- message   : {status.get('message')}
- d3Log     : {status.get('d3Log')}
- pythonLog : {status.get('pythonLog')}
""")
        ret_val: dict|None = data.get("returnValue")
        if ret_val is None:
            raise RuntimeError("Empty returnValue")

        return json.loads(ret_val)

def d3function(module_name: str = "") -> Callable[[Callable[P, T]], D3Function[P, T]]:
    """Decorator to wrap a Python function for D3 Designer execution.
    
    This decorator transforms a regular Python function into a D3Function that can be
    registered with D3 Designer and executed remotely.
    
    Args:
        module_name: Optional module name to register the function under. 
                    If empty, the function will be treated as standalone script and won't be registered.
                    
    Returns:
        A decorator function that wraps the target function in a D3Function.
        
    Example:
        ```
        @d3function("my_d3module")
        def capture_image(self, cam_name: str) -> str:
            import d3
            camera = d3.resourceManager.load(
                d3.Path('objects/camera/{cam_name}.apx'),
                d3.Camera
            )
            return camera.uid
        ```
    """
    def decorator(func: Callable[P, T]) -> D3Function[P, T]:
        return D3Function(module_name, func)
    return decorator


def register_module_d3functions(ipaddr: str, module_name: str) -> tuple[bool, str]:
    """Register all d3function in a module with a Designer instance.
    
    Args:
        ipaddr: IP address of the Designer instance.
        module_name: Name of the module to register.
        
    Returns:
        Tuple containing success status and error message (empty if successful).
    """
    # function with no module shouldn't be registered
    if len(module_name) == 0:
        return (True, "")
    
    try:
        response = requests.post(
            url=f"http://{ipaddr}/api/session/python/registermodule", 
            json=D3Function.get_module_register_blob(module_name)
        )
        return (response.ok, "")
    except Exception as e:
        return (False, str(e))


def register_all_d3functions(ipaddr:str) -> dict[str, tuple[bool, str]]:
    """Register all available d3function across all modules with a Designer instance.
    If d3function was registered without module_name, it won't be registered. 
    
    Args:
        ipaddr: IP address of the Designer instance.
        
    Returns:
        Dictionary mapping module names to registration results (success status and error message).
    """
    responses: dict[str, tuple[bool, str]] = {}
    D3Function._registered_ipaddr = ipaddr
    for module_name in D3Function._available_d3functions.keys():
        responses[module_name] = register_module_d3functions(ipaddr, module_name)
    return responses


def get_all_d3functions() -> list[tuple[str, str]]:
    """Retrieve all available d3function as module_name-function_name pairs.
    
    Returns:
        List of tuples containing (module_name, function_name) for all registered D3 functions.
    """
    module_function_pairs: list[tuple[str, str]] = []
    for module_name, funcs in D3Function._available_d3functions.items():
        module_function_pairs += [(module_name, func.function_info.name) for func in funcs]
    return module_function_pairs


def get_all_modules() -> list[str]:
    """Retrieve name of all module registered with @d3function decorator
    
    Returns:
        List of module names
    """
    return [module_name for module_name in D3Function._available_d3functions.keys()]
