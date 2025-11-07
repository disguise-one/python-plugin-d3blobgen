"""D3 Plugin Client Module

This module provides a metaclass-based framework for creating remote plugin clients
that communicate with D3 Designer. It uses Python's AST manipulation to:

1. Extract and parse source code of plugin classes at definition time
2. Convert Python 3 async methods to Python 2.7 compatible sync code
3. Dynamically wrap user-defined methods to execute remotely via D3 API
4. Generate module registration code for the D3 Designer runtime

The main components are:
- D3PluginClientMeta: Metaclass that handles source code extraction and method wrapping
- D3PluginClient: Base class for creating plugin clients with context manager support

Example:
    class MyPlugin(D3PluginClient):
        module_name = "MyCustomPlugin"

        def __init__(self, hostname: str, port: int, config: str):
            super().__init__(hostname, port)
            self.config = config

        async def process_data(self, data: str) -> int:
            return len(data)

    async with MyPlugin("localhost", 8080, "config") as plugin:
        result = await plugin.process_data("hello")
"""

import ast
import functools
import inspect
import types
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, get_type_hints

from d3blobgen.ast_utils import (
    convert_class_to_py27,
    filter_base_classes,
    filter_init_args,
    get_class_node,
    get_source,
    init_args_to_exclude,
    is_exclude_class_var,
)
from d3blobgen.models import PluginResponse, TypedBlob
from d3blobgen.api import (
    d3_api_aplugin,
    d3_api_aregister_module,
    d3_api_plugin,
    d3_api_register_module,
)

P = ParamSpec("P")
T = TypeVar("T")


def create_d3_plugin_method_wrapper(method_name: str, original_method: Callable[P, T]):
    """Create a wrapper that executes a method remotely via D3 API calls.

    This wrapper intercepts method calls and instead of executing locally:
    1. Serializes the arguments using repr()
    2. Builds a script string in the form: "return plugin.{method_name}({args})"
    3. Creates a TypedBlob with the script and module information
    4. Sends it to D3 Designer via d3_api_plugin or d3_api_aplugin
    5. Returns the result from the remote execution

    Args:
        method_name: Name of the method to wrap
        original_method: The original method object (used for type hints and async detection)

    Returns:
        An async wrapper if the original method is async, otherwise a sync wrapper.
        Both wrappers preserve the original method's metadata via functools.wraps.
    """

    def _build_blob(self, args, kwargs) -> TypedBlob[T]:
        """Helper to build TypedBlob for both sync and async wrappers"""
        # Serialize arguments to string representation for remote execution
        args_parts = [repr(arg) for arg in args]
        kwargs_parts = [f"{key}={repr(value)}" for key, value in kwargs.items()]
        all_args = ", ".join(args_parts + kwargs_parts)

        # Build the Python script that will execute remotely on D3 Designer
        script = f"return plugin.{method_name}({all_args})"

        # Extract return type annotation from the original method for type safety
        type_hints = get_type_hints(original_method)
        return_type = type_hints.get("return", Any)

        # Create TypedBlob containing script, module info, and return type
        return TypedBlob[T](
            json={"moduleName": self.module_name, "script": script},
            return_type=return_type,
            module_name=self.module_name,
        )

    # Determine whether to create async or sync wrapper based on original method
    if inspect.iscoroutinefunction(original_method):
        # Create async wrapper that uses async D3 API call
        @functools.wraps(original_method)
        async def async_wrapper(self, *args, **kwargs):
            blob = _build_blob(self, args, kwargs)
            response: PluginResponse[T] = await d3_api_aplugin(self.hostname, self.port, blob)
            return response.returnValue

        return async_wrapper
    else:
        # Create sync wrapper that uses synchronous D3 API call
        @functools.wraps(original_method)
        def sync_wrapper(self, *args, **kwargs):
            blob = _build_blob(self, args, kwargs)
            response: PluginResponse[T] = d3_api_plugin(self.hostname, self.port, blob)
            return response.returnValue

        return sync_wrapper


class D3PluginClientMeta(type):
    """Metaclass for D3 plugin clients that enables remote method execution.

    This metaclass intercepts class creation to perform several transformations:

    1. Source Code Extraction:
       - Extracts the source code of the class being defined using frame inspection
       - Parses it into an AST for manipulation

    2. Code Filtering:
       - Removes client-side-only class variables (e.g., module_name)
       - Filters out client-side-only __init__ parameters (hostname, port)

    3. Python 2.7 Conversion:
       - Converts async methods to sync for D3 Designer's Python 2.7 runtime
       - Generates both Python 3 and Python 2.7 versions of the source code

    4. Method Wrapping:
       - Wraps all user-defined methods to execute remotely via D3 API
       - Preserves async/sync nature of original methods

    5. Code Generation:
       - Creates templates for instantiating the plugin on the remote side
       - Stores metadata needed for module registration

    Class Attributes (set dynamically on subclasses):
        filtered_init_args: List of __init__ parameter names after filtering
        source_code: Python 3 source code with filtered variables
        source_code_py27: Python 2.7 compatible source code
        module_name: Name used to register the module with D3 Designer
        instance_code_template: Template string for instantiating the plugin remotely
        instance_code: Actual instantiation code with concrete argument values
    """

    # Type hints for dynamically set class attributes
    filtered_init_args: list[str]
    source_code: str
    source_code_py27: str
    module_name: str
    instance_code_template: str
    instance_code: str

    def __new__(cls, name, bases, attrs):
        # Use class name as default module_name if not explicitly provided
        if not attrs.get("module_name"):
            attrs["module_name"] = name

        # Get the caller's frame (where the class is being defined in user code)
        frame: types.FrameType | None = inspect.currentframe()
        if not frame:
            raise ValueError(f"D3PluginClientMeta: Failed to extract source code for {name}")

        caller_frame = frame.f_back
        if not caller_frame:
            raise ValueError(f"D3PluginClientMeta: Failed to extract source code for {name}")

        # Extract full source code from the calling frame's file
        source_code: str | None = get_source(caller_frame)
        if not source_code:
            raise ValueError(f"D3PluginClientMeta: Failed to extract source code for {name}")

        # Parse source code into Abstract Syntax Tree for manipulation
        tree: ast.Module = ast.parse(source_code)

        # Locate the specific class definition node within the AST
        class_node: ast.ClassDef | None = get_class_node(tree, name)
        if not class_node:
            raise ValueError(f"D3PluginClientMeta: Failed to find class definition for {name}")

        # Remove client-side-only class variables (e.g., module_name) from the AST
        class_node.body = [node for node in class_node.body if not is_exclude_class_var(node)]

        # Remove all base class for now as we don't support inheritance
        filter_base_classes(class_node)

        # Filter out client-side-only __init__ arguments and get remaining params
        filtered_init_args: list[str] = filter_init_args(class_node)
        formated_filtered_init_args = [f"{{{arg}}}" for arg in filtered_init_args]

        # Unparse modified AST back to Python 3 source code (clean, no comments)
        attrs["source_code"] = f"{ast.unparse(class_node)}"
        # Create template for instantiating the plugin remotely with placeholders
        attrs["instance_code_template"] = (
            f"plugin = {name}({','.join(formated_filtered_init_args)})"
        )
        attrs["filtered_init_args"] = filtered_init_args

        # Convert async methods to Python 2.7 compatible sync methods
        convert_class_to_py27(class_node)
        attrs["source_code_py27"] = f"{ast.unparse(class_node)}"

        # Wrap all user-defined public methods to execute remotely via D3 API
        # Skip private methods (_*) and internal framework methods
        for attr_name, attr_value in attrs.items():
            if (
                callable(attr_value)
                and not attr_name.startswith("_")
                and attr_name not in ["get_register_module_blob", "get_register_module_content"]
            ):
                attrs[attr_name] = create_d3_plugin_method_wrapper(attr_name, attr_value)

        return super().__new__(cls, name, bases, attrs)

    def __call__(cls, *args, **kwargs):
        """Create an instance and generate its remote instantiation code.

        This method is called when a class instance is created (e.g., MyPlugin(...)).
        It maps the provided arguments to the filtered parameter names and generates
        the instance_code that will be used to instantiate the plugin remotely.

        Args:
            *args: Positional arguments for the plugin __init__
            **kwargs: Keyword arguments for the plugin __init__

        Returns:
            An instance of the plugin class with instance_code attribute set
        """
        # Build mapping from parameter names to their repr() values for remote instantiation
        param_names: list[str] = cls.filtered_init_args
        arg_mapping: dict[str, str] = {}

        # Map positional arguments (skip first N args which are client-side only: hostname, port)
        for i, param_name in enumerate(param_names):
            filtered_idx = i + len(init_args_to_exclude)  # Account for excluded client-side args
            if filtered_idx < len(args):
                arg_mapping[param_name] = repr(args[filtered_idx])

        # Map keyword arguments that match filtered parameter names
        for key, value in kwargs.items():
            if key in param_names:
                arg_mapping[key] = repr(value)

        # Replace placeholders in template with actual serialized argument values
        instance_code = cls.instance_code_template.format(**arg_mapping)

        # Create the actual client instance with all original arguments
        instance = super().__call__(*args, **kwargs)

        # Attach the generated instance_code for use during module registration
        instance.instance_code = instance_code

        return instance


class D3PluginClient(metaclass=D3PluginClientMeta):
    """Base class for creating D3 Designer plugin clients.

    This class provides the foundation for building plugins that execute remotely
    on D3 Designer. When you subclass D3PluginClient, the metaclass automatically:
    - Extracts and processes your class source code
    - Converts it to Python 2.7 compatible code
    - Wraps all your methods to execute remotely
    - Manages module registration with D3 Designer

    Usage:
        class MyPlugin(D3PluginClient):
            module_name = "MyCustomPlugin"  # Optional, defaults to class name

            def __init__(self, hostname: str, port: int, config: dict):
                super().__init__(hostname, port)
                self.config = config

            async def process(self, data: str) -> int:
                # This method will execute remotely on D3 Designer
                return len(data)

        # Use as async context manager
        async with MyPlugin("localhost", 8080, {"key": "value"}) as plugin:
            result = await plugin.process("hello")

        # Or use as sync context manager
        with MyPlugin("localhost", 8080, {"key": "value"}) as plugin:
            result = plugin.process("hello")

    Attributes:
        hostname: The D3 Designer hostname to connect to
        port: The D3 Designer port to connect to
        module_name: The name used to register the module (set by metaclass)
        instance_code: The code used to instantiate the plugin remotely (set on init)

    Note:
        The __init__ method must call super().__init__(hostname, port) and can
        accept additional parameters. The hostname and port are client-side only
        and won't be passed to the remote plugin instance.
    """

    def __init__(self, hostname: str, port: int):
        self.hostname: str = hostname
        self.port: int = port

    async def __aenter__(self):
        """Async context manager entry: registers the module with D3 Designer.

        Returns:
            Self for use in 'async with' statements
        """
        await d3_api_aregister_module(self.hostname, self.port, self.get_register_module_blob())
        print("Entering D3PluginModule context")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Async context manager exit: cleanup operations.

        Args:
            exc_type: Exception type if an exception occurred
            exc: Exception instance if an exception occurred
            tb: Traceback if an exception occurred
        """
        print("Exiting D3PluginModule context")

    def __enter__(self):
        """Sync context manager entry: registers the module with D3 Designer.

        Returns:
            Self for use in 'with' statements
        """
        d3_api_register_module(self.hostname, self.port, self.get_register_module_blob())
        print("Entering D3PluginModule context")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Sync context manager exit: cleanup operations.

        Args:
            exc_type: Exception type if an exception occurred
            exc_value: Exception instance if an exception occurred
            exc_traceback: Traceback if an exception occurred
        """
        print("Exiting D3PluginModule context")

    def get_register_module_blob(self) -> dict[str, str]:
        """Build the module registration blob for D3 Designer.

        Returns:
            Dictionary containing moduleName and contents for registration
        """
        return {
            "moduleName": self.module_name,  # type: ignore[attr-defined]
            "contents": self.get_register_module_content(),
        }

    def get_register_module_content(self) -> str:
        """Generate the complete module content to register with D3 Designer.

        This combines the Python 2.7 compatible class definition with the
        instance creation code.

        Returns:
            String containing the full module code to execute on D3 Designer
        """
        return f"{self.source_code_py27}\n\n{self.instance_code}"  # type: ignore[attr-defined]
