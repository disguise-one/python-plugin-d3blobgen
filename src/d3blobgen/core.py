"""D3 Plugin Core Module

This module contains the core functionality for the D3 plugin system:

- D3Function: Wrapper class for functions that execute remotely
- d3function: Decorator for marking functions as D3-executable
- FunctionInfo: Container for parsed function information
- Package discovery and registration utilities
- Module registration functions

The main entry point is the @d3function decorator, which wraps Python functions
to execute remotely on D3 Designer instances.
"""

import ast
import functools
import inspect
import textwrap
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Generic, ParamSpec, TypeVar, get_type_hints, overload

from pydantic import BaseModel, Field

from d3blobgen.ast_utils import convert_function_to_py27, find_packages_in_current_file
from d3blobgen.api import d3_api_register_module, d3_api_aregister_module
from d3blobgen.models import TypedBlob, PluginRegisterResponse


###############################################################################
# Plugin function related implementations
class FunctionInfo(BaseModel):
    """Container for parsed function information extracted from Python source code.

    This model holds all the essential components of a function after parsing,
    including its complete definition, name, body statements, and argument list.
    """

    blob: str = Field(
        description="full body of function blob without decorator (Function definition + body)"
    )
    blob_py27: str = Field(
        description="full body of function blob without decorator in python2.7 format (Function definition + body)"
    )
    name: str = Field(description="name of extracted function")
    body: str = Field(description="body of extracted function in str format")
    body_py27: str = Field(description="body of extracted function in python2.7 str format")
    args: list[str] = Field(default=[], description="list of arguments from extracted function")


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
    if not isinstance(first_node, ast.FunctionDef) and not isinstance(first_node, ast.AsyncFunctionDef):
        raise ValueError(f"Given input is not a function\ninput:{source_code}")

    # Extract function blob without decorator
    first_node.decorator_list.clear()

    # Extract blob in python 3 format
    blob: str = ast.unparse(first_node)

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

    first_node_py27 = convert_function_to_py27(first_node)
    blob_py27: str = ast.unparse(first_node_py27)

    body_py27 = ""
    for stmt in body_nodes:
        body_py27 += ast.unparse(stmt) + "\n"

    return FunctionInfo(
        blob=blob,
        blob_py27=blob_py27,
        name=function_name,
        body=body.strip(),
        body_py27=body_py27,
        args=args,
    )


P = ParamSpec("P")
T = TypeVar("T")


class D3Function(Generic[P, T]):
    """Wrapper class for Python functions to be executed in Designer environment.

    This class transforms regular Python functions into Designer plugin compatible functions
    that can be registered as modules and executed remotely. It preserves function metadata
    and provides methods for generating execution blobs and registration data.
    """

    _available_packages: defaultdict[str, set[str]] = defaultdict(set)
    _available_d3functions: defaultdict[str, set["D3Function"]] = defaultdict(set)
    _registered_ipaddr: str = "localhost"

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
        self._is_module_function: bool = len(module_name) > 0

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
    def get_module_register_json(module_name: str) -> dict[str, str] | None:
        """Generate a registration blob for all functions in a specific module.

        Args:
            module_name: The name of the module to generate the blob for.

        Returns:
            Dictionary containing module name and all d3function registered under module.
        """
        if module_name not in D3Function._available_d3functions:
            return None

        contents_packages: str = "\n".join(list(D3Function._available_packages[module_name]))
        contents_functions: str = "\n\n".join(
            [
                func.function_info.blob_py27
                for func in D3Function._available_d3functions[module_name]
            ]
        )
        return {
            "moduleName": module_name,
            "contents": f"{contents_packages}\n\n{contents_functions}",
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

    def json(self, *args: P.args, **kwargs: P.kwargs) -> dict[str, str]:
        """Generate an execution blob for running this function in Designer.

        Returns:
            - **module execute blob** if @d3function was registered with module_name
            - **script execute blob** if @d3function was registered without module_name
        """
        if self._is_module_function:
            return {
                "moduleName": self._module_name,
                "script": f"return {self._function_info.name}({self._args_to_string(*args, **kwargs)})",
            }
        else:
            all_args: str = self._args_to_assign(*args, **kwargs)
            return {"script": f"{all_args}\n{self._function_info.body_py27}"}

    def blob(self, *args: P.args, **kwargs: P.kwargs) -> TypedBlob[T]:
        """Generate an execution blob with the return type extracted from function annotations.

        Returns:
            Tuple containing:
            - Execution blob dictionary
            - The return type class/type from the function's type hints (or Any if not annotated)
        """

        return TypedBlob[T](
            json=self.json(*args, **kwargs),
            module_name=self.module_name,
        )


###############################################################################
# d3function API

# Overload for when used without parentheses: @d3function
@overload
def d3function(module_name: Callable[P, T]) -> D3Function[P, T]: ...

# Overload for when used with parentheses: @d3function() or @d3function("module_name")
@overload
def d3function(module_name: str = "") -> Callable[[Callable[P, T]], D3Function[P, T]]: ...

# Actual implementation
def d3function(
    module_name: str | Callable[P, T] = ""
) -> D3Function[P, T] | Callable[[Callable[P, T]], D3Function[P, T]]:
    """Decorator to wrap a Python function for D3 Designer execution.

    This decorator transforms a regular Python function into a D3Function that can be
    registered with D3 Designer and executed remotely. It can be used with or without
    parentheses.

    Args:
        module_name: Optional module name to register the function under.
                    If empty, the function will be treated as standalone script and won't be registered.
                    When used without parentheses (@d3function), this parameter receives the decorated function.

    Returns:
        A D3Function instance or a decorator function that wraps the target function in a D3Function.

    Examples:
        ```
        # With module name
        @d3function("my_d3module")
        def capture_image(cam_name: str) -> str:
            import d3
            camera = d3.resourceManager.load(
                d3.Path('objects/camera/{cam_name}.apx'),
                d3.Camera
            )
            return camera.uid

        # Without parentheses (standalone)
        @d3function
        def my_add(a: int, b: int) -> int:
            return a + b

        # With empty parentheses (standalone)
        @d3function()
        def my_subtract(a: int, b: int) -> int:
            return a - b
        ```
    """

    def decorator(func: Callable[P, T]) -> D3Function[P, T]:
        return D3Function(actual_module_name, func)

    # Check if module_name is actually a function (decorator used without parentheses)
    if callable(module_name):
        # @d3function (without parentheses)
        actual_module_name = ""
        return D3Function(actual_module_name, module_name)
    else:
        # @d3function() or @d3function("module_name")
        actual_module_name = module_name
        return decorator


def add_packages_in_current_file(module_name: str) -> None:
    """Add all import statements from the caller's file to a D3 module's package list.

    This function scans the calling file's import statements and registers them with
    the specified module name, making those imports available when the module is
    registered with Designer. This is useful for ensuring all dependencies are included
    when deploying Python functions to D3 Designer.

    Args:
        module_name: The name of the D3 module to associate the packages with.
                    Must match the module_name used in @d3function decorator.

    Example:
        ```python
        import numpy as np

        @d3function("my_module")
        def my_function():
            return np.array([1, 2, 3])

        # Register all imports in the file (numpy)
        add_packages_in_current_file("my_module")
        ```
    """
    # caller_stack is 2, 1 for this, 1 for caller of this function.
    packages: list[str] = find_packages_in_current_file(2)
    D3Function._available_packages[module_name].update(packages)


def get_module_register_json(module_name: str) -> dict[str, str] | None:
    return D3Function.get_module_register_json(module_name)

def register_all_d3functions(ipaddr: str, port: int) -> dict[str, PluginRegisterResponse]:
    """Register all available d3function across all modules with a Designer instance.
    If d3function was registered without module_name, it won't be registered.

    Args:
        ipaddr: IP address of the Designer instance.

    Returns:
        Dictionary mapping module names to registration results (success status and error message).
    """
    responses: dict[str, PluginRegisterResponse] = {}
    D3Function._registered_ipaddr = ipaddr
    for module_name in D3Function._available_d3functions.keys():
        register_blob: dict[str, str] | None = D3Function.get_module_register_json(module_name)
        if register_blob:
            responses[module_name] = d3_api_register_module(ipaddr, port,register_blob)

    return responses


async def aregister_all_d3functions(ipaddr: str, port: int) -> dict[str, PluginRegisterResponse]:
    """Asynchronously register all available d3function across all modules with a Designer instance.
    If d3function was registered without module_name, it won't be registered.

    Args:
        ipaddr: IP address of the Designer instance.

    Returns:
        Dictionary mapping module names to registration results (success status and error message).
    """
    responses: dict[str, PluginRegisterResponse] = {}
    D3Function._registered_ipaddr = ipaddr
    for module_name in D3Function._available_d3functions.keys():
        responses[module_name] = await d3_api_aregister_module(ipaddr, port, D3Function.get_module_register_json(module_name))
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
    return list(D3Function._available_d3functions.keys())
