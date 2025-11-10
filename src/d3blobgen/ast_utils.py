"""AST Manipulation Utilities Module

This module provides utilities for manipulating Python Abstract Syntax Trees (AST),
primarily for converting Python 3 code to Python 2.7 compatible format. This includes:

- Removing type hints and annotations
- Converting async functions to sync functions
- Extracting and filtering class/function definitions
- Source code inspection and manipulation

These utilities are used by both the D3Function decorator and D3PluginClient metaclass
to prepare Python code for execution in D3 Designer's Python 2.7 runtime.
"""

import ast
import inspect
import textwrap
import types


###############################################################################
# Configuration for filtering client-side-only constructs

class_vars_to_exclude: set[str] = {"module_name"}
"""Class variables that should be excluded from the source code sent to D3 Designer."""

init_args_to_exclude: set[str] = {"hostname", "port"}
"""Arguments that should be excluded from __init__ when registering with D3 Designer.

These arguments are client-side only and not needed by the remote plugin instance.
"""


###############################################################################
# Source code extraction utilities


def get_source(frame: types.FrameType) -> str | None:
    """Extract and dedent source code from a frame object.

    Args:
        frame: The frame object to extract source code from

    Returns:
        Dedented source code as a string, or None if source cannot be found

    Raises:
        OSError: If the source file cannot be found or read
    """
    source_lines, _ = inspect.findsource(frame)
    return textwrap.dedent("".join(source_lines)) if source_lines else None


def get_class_node(tree, class_name: str) -> ast.ClassDef | None:
    """Find a class definition node by name in an AST.

    Args:
        tree: The AST tree to search
        class_name: The name of the class to find

    Returns:
        The ClassDef node if found, None otherwise
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


###############################################################################
# AST node filtering utilities


def is_exclude_class_var(node: ast.stmt) -> bool:
    """Check if an AST node represents a class variable that should be excluded.

    Args:
        node: AST statement node to check

    Returns:
        True if the node is an excluded class variable, False otherwise
    """
    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id in class_vars_to_exclude:
            return True
    elif isinstance(node, ast.Assign):
        if any(
            isinstance(target, ast.Name) and target.id in class_vars_to_exclude
            for target in node.targets
        ):
            return True
    return False


def is_exclude_arg(arg: ast.expr) -> bool:
    """Check if an AST expression node represents an excluded argument.

    Args:
        arg: AST expression node to check

    Returns:
        True if the argument is in the exclusion list, False otherwise
    """
    return isinstance(arg, ast.Name) and arg.id in init_args_to_exclude

def filter_base_classes(class_node: ast.ClassDef):
    """Remove all base classes as we won't support the inheritance at the moment.
    
    Args:
        class_node: The class definition node to process
    """
    class_node.bases = []

def filter_init_args(class_node: ast.ClassDef) -> list[str]:
    """Remove excluded arguments from __init__ method and extract parameter names.

    This function modifies the class_node in-place by:
    1. Removing excluded parameters from __init__ signature
    2. Removing excluded arguments from super().__init__() calls
    3. Returning the list of remaining parameter names (excluding 'self')

    Args:
        class_node: The class definition node to process

    Returns:
        List of parameter names that remain after filtering (excluding 'self')
    """
    for node in class_node.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name != "__init__":
            continue

        # Remove super().__init__() calls from the body
        node.body = [
            stmt for stmt in node.body
            if not (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Attribute)
                and stmt.value.func.attr == "__init__"
                and isinstance(stmt.value.func.value, ast.Call)
                and isinstance(stmt.value.func.value.func, ast.Name)
                and stmt.value.func.value.func.id == "super"
            )
        ]

        # Filter out excluded arguments from the parameter list
        node.args.args = [arg for arg in node.args.args if arg.arg not in init_args_to_exclude]

        # Filter keyword-only arguments if present (Python 3+ feature)
        if node.args.kwonlyargs:
            node.args.kwonlyargs = [
                arg for arg in node.args.kwonlyargs if arg.arg not in init_args_to_exclude
            ]

        # Return filtered parameter names (excluding 'self' which is implicit)
        return [arg.arg for arg in node.args.args if arg.arg != "self"]

    return []


###############################################################################
# Type hint removal utilities


def convert_ann_assign_to_assign(ann_assign_node: ast.AnnAssign) -> ast.Assign | None:
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
        lineno=ann_assign_node.lineno,
        col_offset=ann_assign_node.col_offset,
    )


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


###############################################################################
# Python 2.7 conversion utilities


def convert_function_node_to_py27(function_node: ast.FunctionDef) -> None:
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


def convert_class_to_py27(class_node: ast.ClassDef) -> None:
    """Convert async methods in a class to Python 2.7 compatible sync methods.

    This function modifies the class_node in-place by:
    1. Converting AsyncFunctionDef nodes to FunctionDef nodes
    2. Recursively converting method bodies using convert_function_node_to_py27

    Args:
        class_node: The class definition node to convert
    """
    for i, node in enumerate(class_node.body):
        if isinstance(node, ast.AsyncFunctionDef):
            # Convert AsyncFunctionDef to FunctionDef by creating a new node
            regular_func = ast.FunctionDef(
                name=node.name,
                args=node.args,
                body=node.body,
                decorator_list=node.decorator_list,
                returns=node.returns,
                type_comment=node.type_comment if hasattr(node, "type_comment") else None,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            class_node.body[i] = regular_func
            node = class_node.body[i]

        if isinstance(node, ast.FunctionDef):
            convert_function_node_to_py27(node)


###############################################################################
# Python package finder utility


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
    current_frame: types.FrameType | None = inspect.currentframe()
    if not current_frame:
        return []

    # Get the caller's frame (file where this function is called)
    caller_frame: types.FrameType | None = current_frame
    for _i in range(caller_stack):
        if not caller_frame or not caller_frame.f_back:
            return []
        caller_frame = caller_frame.f_back

    if not caller_frame:
        return []

    modules: types.ModuleType | None = inspect.getmodule(caller_frame)
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