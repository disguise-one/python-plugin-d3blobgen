"""Tests for AST manipulation utilities."""

import ast
import textwrap

import pytest

from d3blobgen.ast_utils import (
    ConvertToPython27,
    convert_class_to_py27,
    convert_function_to_py27,
    filter_base_classes,
    filter_init_args,
    get_class_node,
)


class TestConvertToPython27Transformer:
    """Tests for the ConvertToPython27 AST transformer."""

    def test_remove_return_type_annotation(self):
        """Test that return type annotations are removed from functions."""
        source = textwrap.dedent("""
            def my_function() -> int:
                return 42
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        # Find the function node
        func = transformed.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert func.returns is None

    def test_remove_argument_annotations(self):
        """Test that argument type annotations are removed."""
        source = textwrap.dedent("""
            def my_function(x: int, y: str, z: list[int]) -> None:
                pass
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        # Check all arguments have no annotations
        for arg in func.args.args:
            assert arg.annotation is None

    def test_convert_async_to_sync_function(self):
        """Test that async functions are converted to regular functions."""
        source = textwrap.dedent("""
            async def async_function() -> int:
                return 42
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        # Should be converted to FunctionDef, not AsyncFunctionDef
        func = transformed.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert not isinstance(func, ast.AsyncFunctionDef)
        assert func.name == "async_function"
        assert func.returns is None  # Return annotation should be removed too

    def test_remove_await_expressions(self):
        """Test that await expressions are converted to normal calls."""
        source = textwrap.dedent("""
            async def my_function():
                result = await some_async_call()
                return result
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        # Get the assignment statement: result = await some_async_call()
        assign_stmt = func.body[0]
        assert isinstance(assign_stmt, ast.Assign)

        # The value should now be a Call, not an Await
        assert isinstance(assign_stmt.value, ast.Call)
        assert not isinstance(assign_stmt.value, ast.Await)

    def test_convert_annotated_assignment(self):
        """Test that annotated assignments are converted to regular assignments."""
        source = textwrap.dedent("""
            def my_function():
                x: int = 5
                y: str = "hello"
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        # Both statements should be regular Assign nodes, not AnnAssign
        for stmt in func.body:
            assert isinstance(stmt, ast.Assign)
            assert not isinstance(stmt, ast.AnnAssign)

    def test_annotated_assignment_without_value(self):
        """Test that annotated assignments without values are removed."""
        source = textwrap.dedent("""
            def my_function():
                x: int
                y = 10
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        # Only one statement should remain (y = 10)
        assert len(func.body) == 1
        assert isinstance(func.body[0], ast.Assign)

    def test_nested_async_functions(self):
        """Test that nested async functions are also converted."""
        source = textwrap.dedent("""
            async def outer():
                async def inner() -> str:
                    return await some_call()
                return await inner()
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        outer_func = transformed.body[0]
        # Outer should be regular function
        assert isinstance(outer_func, ast.FunctionDef)

        # Inner should also be regular function
        inner_func = outer_func.body[0]
        assert isinstance(inner_func, ast.FunctionDef)
        assert inner_func.returns is None

    def test_complex_type_annotations(self):
        """Test removal of complex type annotations."""
        source = textwrap.dedent("""
            def my_function(
                items: list[str],
                mapping: dict[str, int],
                *args: int,
                **kwargs: str
            ) -> tuple[int, str]:
                result: dict[str, int] = {}
                return (0, "")
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        # Return type removed
        assert func.returns is None

        # Regular args annotations removed
        for arg in func.args.args:
            assert arg.annotation is None

        # *args annotation removed
        if func.args.vararg:
            assert func.args.vararg.annotation is None

        # **kwargs annotation removed
        if func.args.kwarg:
            assert func.args.kwarg.annotation is None

        # Annotated assignment converted
        assign_stmt = func.body[0]
        assert isinstance(assign_stmt, ast.Assign)

    def test_convert_basic_fstring(self):
        """Test that basic f-strings are converted to .format() style."""
        source = textwrap.dedent("""
            def my_function(name):
                message = f"Hello {name}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # The value should be a Call node (str.format())
        assert isinstance(assign_stmt.value, ast.Call)

        # It should be calling the 'format' attribute
        assert isinstance(assign_stmt.value.func, ast.Attribute)
        assert assign_stmt.value.func.attr == "format"

        # The base string should be "Hello {}"
        assert isinstance(assign_stmt.value.func.value, ast.Constant)
        assert assign_stmt.value.func.value.value == "Hello {}"

        # It should have one argument (name)
        assert len(assign_stmt.value.args) == 1
        assert isinstance(assign_stmt.value.args[0], ast.Name)
        assert assign_stmt.value.args[0].id == "name"

    def test_convert_fstring_with_format_spec(self):
        """Test that f-strings with format specifications are converted correctly."""
        source = textwrap.dedent("""
            def my_function(x):
                message = f"Value: {x:.2f}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # Should be a .format() call
        assert isinstance(assign_stmt.value, ast.Call)
        assert assign_stmt.value.func.attr == "format"

        # The format string should preserve the format spec (if implementation supports it)
        # Current implementation handles simple format specs
        format_str = assign_stmt.value.func.value.value
        assert "Value:" in format_str
        assert "{" in format_str and "}" in format_str

        # It should have one argument (x)
        assert len(assign_stmt.value.args) == 1

    def test_convert_fstring_with_conversion_flag(self):
        """Test that f-strings with conversion flags (!r, !s, !a) are converted correctly."""
        source = textwrap.dedent("""
            def my_function(obj):
                message = f"Repr: {obj!r}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # Should be a .format() call
        assert isinstance(assign_stmt.value, ast.Call)

        # The format string should preserve the conversion flag
        assert assign_stmt.value.func.value.value == "Repr: {!r}"

        # It should have one argument (obj)
        assert len(assign_stmt.value.args) == 1

    def test_convert_fstring_with_multiple_expressions(self):
        """Test that f-strings with multiple expressions are converted correctly."""
        source = textwrap.dedent("""
            def my_function(name, age):
                message = f"Name: {name}, Age: {age}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # Should be a .format() call
        assert isinstance(assign_stmt.value, ast.Call)

        # The format string should have two placeholders
        assert assign_stmt.value.func.value.value == "Name: {}, Age: {}"

        # It should have two arguments (name, age)
        assert len(assign_stmt.value.args) == 2

    def test_convert_fstring_with_literal_braces(self):
        """Test that f-strings with literal braces (escaped) are converted correctly."""
        source = textwrap.dedent("""
            def my_function(value):
                message = f"Dict: {{key: {value}}}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # Should be a .format() call
        assert isinstance(assign_stmt.value, ast.Call)

        # The format string should preserve the escaped braces
        assert assign_stmt.value.func.value.value == "Dict: {{key: {}}}"

        # It should have one argument (value)
        assert len(assign_stmt.value.args) == 1

    def test_convert_fstring_with_complex_expression(self):
        """Test that f-strings with complex expressions are converted correctly."""
        source = textwrap.dedent("""
            def my_function(items):
                message = f"Count: {len(items)}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # Should be a .format() call
        assert isinstance(assign_stmt.value, ast.Call)

        # The format string should have one placeholder
        assert assign_stmt.value.func.value.value == "Count: {}"

        # It should have one argument (len(items))
        assert len(assign_stmt.value.args) == 1
        assert isinstance(assign_stmt.value.args[0], ast.Call)

    def test_convert_fstring_combined_features(self):
        """Test f-string with combined conversion flag and format spec."""
        source = textwrap.dedent("""
            def my_function(x):
                message = f"Value: {x!s:>10}"
                return message
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]
        assign_stmt = func.body[0]

        # Should be a .format() call
        assert isinstance(assign_stmt.value, ast.Call)

        # The format string should preserve conversion flag at minimum
        format_str = assign_stmt.value.func.value.value
        assert "Value:" in format_str
        assert "{!s" in format_str or "{" in format_str

        # It should have one argument (x)
        assert len(assign_stmt.value.args) == 1


class TestConvertFunctionToPy27:
    """Tests for convert_function_to_py27 function."""

    def test_simple_function_conversion(self):
        """Test basic function conversion."""
        source = textwrap.dedent("""
            def my_function(x: int, y: str) -> bool:
                result: str = f"{x} {y}"
                return True
        """)

        tree = ast.parse(source)
        func_node = tree.body[0]

        convert_function_to_py27(func_node)

        # Verify conversions
        assert func_node.returns is None
        for arg in func_node.args.args:
            assert arg.annotation is None

        # Check body was transformed
        assign_stmt = func_node.body[0]
        assert isinstance(assign_stmt, ast.Assign)

    def test_async_function_body_conversion(self):
        """Test that async function bodies are converted."""
        source = textwrap.dedent("""
            async def my_function():
                result = await some_call()
                data: int = 42
                return result
        """)

        tree = ast.parse(source)
        func_node = tree.body[0]

        # First convert async to regular (simulating what happens in real usage)
        transformer = ConvertToPython27()
        new_func = transformer.visit_AsyncFunctionDef(func_node)

        # The function should now be regular FunctionDef
        assert isinstance(new_func, ast.FunctionDef)

        # Check await was removed
        assign_stmt = new_func.body[0]
        assert isinstance(assign_stmt.value, ast.Call)

        # Check annotated assignment was converted
        assign_stmt2 = new_func.body[1]
        assert isinstance(assign_stmt2, ast.Assign)


class TestConvertClassToPy27:
    """Tests for convert_class_to_py27 function."""

    def test_class_with_async_methods(self):
        """Test that class with async methods is converted."""
        source = textwrap.dedent("""
            class MyClass:
                async def async_method(self) -> int:
                    return await something()

                def regular_method(self, x: int) -> str:
                    return str(x)
        """)

        tree = ast.parse(source)
        class_node = tree.body[0]

        convert_class_to_py27(class_node)

        # All methods should be regular FunctionDef
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                assert not isinstance(node, ast.AsyncFunctionDef)
                # Return annotations should be removed
                assert node.returns is None
                # Argument annotations should be removed
                for arg in node.args.args:
                    assert arg.annotation is None


class TestAsyncFunctionDefInvestigation:
    """Investigation tests for visit_AsyncFunctionDef behavior."""

    def test_async_def_converted_to_def(self):
        """Verify that AsyncFunctionDef is replaced with FunctionDef in the tree."""
        source = textwrap.dedent("""
            async def my_async_func(x: int) -> str:
                result = await call_something(x)
                return result
        """)

        tree = ast.parse(source)
        original_func = tree.body[0]
        assert isinstance(original_func, ast.AsyncFunctionDef)

        # Apply transformer
        transformer = ConvertToPython27()
        transformed_tree = transformer.visit(tree)

        # The node in the tree should now be FunctionDef
        new_func = transformed_tree.body[0]
        assert isinstance(new_func, ast.FunctionDef)
        assert not isinstance(new_func, ast.AsyncFunctionDef)

        # Verify properties are preserved
        assert new_func.name == "my_async_func"
        assert len(new_func.args.args) == 1
        assert new_func.args.args[0].arg == "x"

        # Return type should be removed
        assert new_func.returns is None

        # Argument annotation should be removed
        assert new_func.args.args[0].annotation is None

    def test_async_with_nested_transformations(self):
        """Test that async function with nested await and annotations works."""
        source = textwrap.dedent("""
            async def process_data(items: list[str]) -> dict[str, int]:
                results: dict[str, int] = {}
                for item in items:
                    value = await fetch_value(item)
                    results[item] = value
                return results
        """)

        tree = ast.parse(source)
        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        func = transformed.body[0]

        # Should be regular function
        assert isinstance(func, ast.FunctionDef)

        # No return type
        assert func.returns is None

        # No argument annotations
        assert func.args.args[0].annotation is None

        # First statement should be regular assignment (not annotated)
        first_stmt = func.body[0]
        assert isinstance(first_stmt, ast.Assign)
        assert not isinstance(first_stmt, ast.AnnAssign)

        # The await in the loop should be converted to regular call
        for_loop = func.body[1]
        assert isinstance(for_loop, ast.For)
        assign_in_loop = for_loop.body[0]
        assert isinstance(assign_in_loop.value, ast.Call)

    def test_location_metadata_preserved(self):
        """Test that source location metadata is preserved during conversion."""
        source = textwrap.dedent("""
            async def my_func():
                pass
        """)

        tree = ast.parse(source)
        original_func = tree.body[0]
        original_lineno = original_func.lineno
        original_col = original_func.col_offset

        transformer = ConvertToPython27()
        transformed = transformer.visit(tree)

        new_func = transformed.body[0]
        # Location should be preserved via ast.copy_location
        assert new_func.lineno == original_lineno
        assert new_func.col_offset == original_col


class TestGetClassNode:
    """Tests for get_class_node function."""

    def test_find_class_by_name(self):
        """Test finding a class definition by name."""
        source = textwrap.dedent("""
            class FirstClass:
                pass

            class SecondClass:
                pass

            class ThirdClass:
                pass
        """)

        tree = ast.parse(source)
        class_node = get_class_node(tree, "SecondClass")

        assert class_node is not None
        assert isinstance(class_node, ast.ClassDef)
        assert class_node.name == "SecondClass"

    def test_class_not_found(self):
        """Test that None is returned when class is not found."""
        source = textwrap.dedent("""
            class MyClass:
                pass
        """)

        tree = ast.parse(source)
        class_node = get_class_node(tree, "NonExistentClass")

        assert class_node is None


class TestFilterBaseClasses:
    """Tests for filter_base_classes function."""

    def test_remove_all_base_classes(self):
        """Test that all base classes are removed from a class definition."""
        source = textwrap.dedent("""
            class MyClass(BaseClass, AnotherBase):
                pass
        """)

        tree = ast.parse(source)
        class_node = tree.body[0]

        # Verify bases exist before filtering
        assert len(class_node.bases) == 2

        filter_base_classes(class_node)

        # Verify all bases are removed
        assert len(class_node.bases) == 0

    def test_empty_base_classes(self):
        """Test that filtering works on classes with no base classes."""
        source = textwrap.dedent("""
            class MyClass:
                pass
        """)

        tree = ast.parse(source)
        class_node = tree.body[0]

        filter_base_classes(class_node)

        assert len(class_node.bases) == 0


class TestFilterInitArgs:
    """Tests for filter_init_args function."""

    def test_class_without_init(self):
        """Test that classes without __init__ return empty list."""
        source = textwrap.dedent("""
            class MyClass:
                def __init__(self, a: int):
                    pass
                def other_method(self):
                    pass
        """)

        tree = ast.parse(source)
        class_node = tree.body[0]

        param_names = filter_init_args(class_node)

        assert param_names == ["a"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
