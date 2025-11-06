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
from types import FrameType, ModuleType
from typing import Any, Generic, ParamSpec, TypeVar, get_type_hints

from pydantic import BaseModel, Field

from d3blobgen.ast_utils import convert_function_node_to_py27
from d3blobgen.utils import d3_api_register_module, d3_api_aregister_module
from d3blobgen.models import TypedBlob



###############################################################################
# import package helpers
def find_packages_in_current_file(caller_stack: int = 1) -> list[str]:
    """Find all import statements in the caller's file by inspecting the call stack.

    This function walks up the call stack to find the module where it was called from,
    then parses that module's source code to extract all import statements.

    Args:
        caller_stack: Number of frames to go up the call stack. Default is 1 (immediate caller).
                     Use higher values to inspect files further up the call chain.

    Returns:
        Sorted list of unique import statement strings (e.g., "import ast", "from pathlib import Path").

    Filters applied:
        - Excludes imports inside `if TYPE_CHECKING:` blocks
        - Excludes imports of this function itself to avoid circular references
    """
    # Get the this file frame
    current_frame: FrameType | None = inspect.currentframe()
    if not current_frame:
        return []

    # Get the caller's frame (file where this function is called)
    caller_frame: FrameType | None = current_frame
    for _i in range(caller_stack):
        if not caller_frame or not caller_frame.f_back:
            return []
        caller_frame = caller_frame.f_back

    if not caller_frame:
        return []

    modules: ModuleType | None = inspect.getmodule(caller_frame)
    if not modules:
        return []

    source: str = inspect.getsource(modules)

    # Parse the source code
    tree = ast.parse(source)

    # Get the name of this function to filter it out
    # For example, we don't want `from core import find_packages_in_current_file`
    function_name: str = current_frame.f_code.co_name
    # Skip any package from d3blobgen
    d3blobgen_package_name: str = "d3blobgen"
    # typing not supported in python2.7
    typing_package_name: str = "typing"

    def is_type_checking_block(node: ast.If) -> bool:
        """Check if an if statement is 'if TYPE_CHECKING:'"""
        return isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"

    imports: list[str] = []
    for node in tree.body:
        # Skip TYPE_CHECKING blocks entirely
        if isinstance(node, ast.If) and is_type_checking_block(node):
            continue

        if isinstance(node, ast.Import):
            imported_modules: list[str] = [alias.name for alias in node.names]
            # Skip imports that include d3blobgen
            if any(d3blobgen_package_name in module for module in imported_modules):
                continue
            if any(typing_package_name in module for module in imported_modules):
                continue
            import_text: str = f"import {', '.join(imported_modules)}"
            imports.append(import_text)

        elif isinstance(node, ast.ImportFrom):
            imported_module: str | None = node.module
            imported_names: list[str] = [alias.name for alias in node.names]
            if not imported_module:
                continue
            # Skip imports that include d3blobgen
            if d3blobgen_package_name in imported_module:
                continue
            elif typing_package_name in imported_module:
                continue
            # Skip imports that include this function itself
            if function_name in imported_names:
                continue

            line_text = f"from {imported_module} import {', '.join(imported_names)}"
            imports.append(line_text)

    return sorted(set(imports))


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
    if not isinstance(first_node, ast.FunctionDef):
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

    convert_function_node_to_py27(first_node)
    blob_py27: str = ast.unparse(first_node)

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

    def __init__(self, module_name: str, timeout_sec: float | None, func: Callable[P, T]):
        """Initialise a D3Function wrapper around a Python function.

        Args:
            module_name: Name of the module to register this function under.
                        Empty string means standalone function execution.
            func: The Python function to wrap for D3 execution.
        """
        self._module_name: str = module_name
        self._timeout_sec: float | None = timeout_sec
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
    def get_module_register_blob(module_name: str) -> dict[str, str]:
        """Generate a registration blob for all functions in a specific module.

        Args:
            module_name: The name of the module to generate the blob for.

        Returns:
            Dictionary containing module name and all d3function registered under module.
        """
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
        type_hints = get_type_hints(self._function)
        return_type = type_hints.get("return", Any)

        return TypedBlob[T](
            json=self.json(*args, **kwargs),
            return_type=return_type,
            module_name=self.module_name,
        )


###############################################################################
# d3function API
def d3function(
    module_name: str = "", timeout_sec: float | None = None
) -> Callable[[Callable[P, T]], D3Function[P, T]]:
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
        return D3Function(module_name, timeout_sec, func)

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


def get_module_register_blob(module_name: str) -> dict[str, str] | None:
    if module_name in D3Function._available_d3functions:
        return D3Function.get_module_register_blob(module_name)
    else:
        return None

def register_all_d3functions(ipaddr: str, port: int) -> dict[str, tuple[bool, str]]:
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
        responses[module_name] = d3_api_register_module(ipaddr, port, D3Function.get_module_register_blob(module_name))
    return responses


async def aregister_all_d3functions(ipaddr: str, port: int) -> dict[str, tuple[bool, str]]:
    """Asynchronously register all available d3function across all modules with a Designer instance.
    If d3function was registered without module_name, it won't be registered.

    Args:
        ipaddr: IP address of the Designer instance.

    Returns:
        Dictionary mapping module names to registration results (success status and error message).
    """
    responses: dict[str, tuple[bool, str]] = {}
    D3Function._registered_ipaddr = ipaddr
    for module_name in D3Function._available_d3functions.keys():
        responses[module_name] = await d3_api_aregister_module(ipaddr, port, D3Function.get_module_register_blob(module_name))
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
