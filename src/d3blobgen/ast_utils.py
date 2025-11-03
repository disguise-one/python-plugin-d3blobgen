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

        # Filter out excluded arguments from the parameter list
        node.args.args = [arg for arg in node.args.args if arg.arg not in init_args_to_exclude]

        # Filter arguments in super().__init__() calls in the body
        for body_node in ast.walk(node):
            if not isinstance(body_node, ast.Call):
                continue
            # Check if this is super().__init__(...) call
            if (
                isinstance(body_node.func, ast.Attribute)
                and body_node.func.attr == "__init__"
                and isinstance(body_node.func.value, ast.Call)
                and isinstance(body_node.func.value.func, ast.Name)
                and body_node.func.value.func.id == "super"
            ):
                # Filter out excluded positional arguments
                body_node.args = [arg for arg in body_node.args if not is_exclude_arg(arg)]

                # Filter out excluded keyword arguments
                body_node.keywords = [
                    kw for kw in body_node.keywords if kw.arg not in init_args_to_exclude
                ]

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

        if isinstance(node, ast.FunctionDef):
            convert_function_node_to_py27(node)
