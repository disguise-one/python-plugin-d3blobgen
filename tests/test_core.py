import pytest
from d3blobgen.core import extract_function_blob, extract_function_info, get_d3_function_blob, FunctionInfo


def example_function():
    """Example function for testing"""
    return "hello world"


def example_function_with_args(name, value):
    """Example function with arguments for testing"""
    return f"Hello {name}, value is {value}"


class TestExtractFunctionBlob:
    
    def test_extract_simple_function(self):
        source = extract_function_blob(example_function)
        assert "def example_function():" in source
        assert "return \"hello world\"" in source
    
    def test_extract_function_with_args(self):
        source = extract_function_blob(example_function_with_args)
        assert "def example_function_with_args(name, value):" in source
        assert "return f\"Hello {name}, value is {value}\"" in source


class TestExtractFunctionInfo:
    
    def test_extract_info_simple_function(self):
        source_code = '''def example_func():
    return "test"'''
        
        info = extract_function_info(source_code)
        
        assert info.name == "example_func"
        assert info.body == "return 'test'"
        assert info.args == []
    
    def test_extract_info_function_with_args(self):
        source_code = '''def example_func(arg1, arg2):
    result = arg1 + arg2
    return result'''
        
        info = extract_function_info(source_code)
        
        assert info.name == "example_func"
        assert "result = arg1 + arg2" in info.body
        assert "return result" in info.body
        assert info.args == ["arg1", "arg2"]
    
    def test_extract_info_invalid_input(self):
        with pytest.raises(ValueError, match="Given input is not a function"):
            extract_function_info("x = 5")
    
    def test_extract_info_empty_input(self):
        with pytest.raises(ValueError, match="Given input is not a function"):
            extract_function_info("")


class TestGetD3FunctionBlob:
    
    def test_get_blob_without_args(self):
        blob = get_d3_function_blob(example_function)
        expected_body = "'Example function for testing'\nreturn 'hello world'"
        assert blob == expected_body
    
    def test_get_blob_with_args(self):
        blob = get_d3_function_blob(example_function_with_args, {"name": "test_name", "value": "test_value"})
        expected_body = "'Example function with arguments for testing'\nreturn f'Hello test_name, value is test_value'"
        assert blob == expected_body
    
    def test_get_blob_args_mismatch(self):
        with pytest.raises(ValueError, match="mismatch between args and function args"):
            get_d3_function_blob(example_function_with_args, {"wrong_arg": "value"})


class TestFunctionInfo:
    
    def test_function_info_creation(self):
        info = FunctionInfo(
            name="test_func",
            body="return 42",
            args=["x", "y"]
        )
        
        assert info.name == "test_func"
        assert info.body == "return 42"
        assert info.args == ["x", "y"]
    
    def test_function_info_defaults(self):
        info = FunctionInfo(name="test_func", body="return 42")
        assert info.args == []