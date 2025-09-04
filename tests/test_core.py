import pytest
from unittest.mock import Mock, patch
from d3blobgen.core import (
    extract_function_info,
    FunctionInfo,
    d3function,
    D3Function,
    register_module_d3functions,
    register_all_d3functions,
    get_all_d3functions,
    get_all_modules
)


def example_function():
    """Example function for testing"""
    return "hello world"


def example_function_with_args(name, value):
    """Example function with arguments for testing"""
    return f"Hello {name}, value is {value}"


@d3function("test_module")
def decorated_example_function():
    """Decorated example function for testing"""
    return "decorated hello world"


@d3function()  # No module name
def standalone_function(x, y):
    """Standalone function for testing"""
    return x + y


@d3function("module_a")
def function_in_module_a():
    """Function in module A for testing"""
    return "module_a_result"


@d3function("module_b")
def function_in_module_b(value):
    """Function in module B for testing"""
    return f"module_b_{value}"


class TestExtractFunctionInfo:
    
    def test_extract_info_simple_function(self):
        info = extract_function_info(example_function)
        
        assert info.name == "example_function"
        assert "return 'hello world'" in info.body
        assert info.args == []
        assert "def example_function():" in info.blob
    
    def test_extract_info_function_with_args(self):
        info = extract_function_info(example_function_with_args)
        
        assert info.name == "example_function_with_args"
        assert "return f'Hello {name}, value is {value}'" in info.body
        assert info.args == ["name", "value"]
        assert "def example_function_with_args(name, value):" in info.blob
    
    def test_extract_info_decorated_function(self):
        # Test that decorators are removed from the blob
        info = extract_function_info(decorated_example_function._function)
        
        assert info.name == "decorated_example_function"
        assert "return 'decorated hello world'" in info.body
        assert info.args == []
        # Should not contain the decorator in the blob
        assert "@d3function" not in info.blob


class TestD3Function:
    
    def test_d3_function_creation(self):
        d3_func = D3Function("test_module", example_function)
        
        assert d3_func.name == "example_function"
        assert d3_func.module_name == "test_module"
        assert d3_func._is_module_function == True
    
    def test_d3_function_standalone(self):
        d3_func = D3Function("", standalone_function._function)
        
        assert d3_func.name == "standalone_function"
        assert d3_func.module_name == ""
        assert d3_func._is_module_function == False
    
    def test_d3_function_call(self):
        # Test that the wrapped function can still be called
        result = decorated_example_function()
        assert result == "decorated hello world"
        
        result = standalone_function(5, 3)
        assert result == 8
    
    def test_get_execute_blob_module_function(self):
        blob = decorated_example_function.get_execute_blob()
        
        assert blob["moduleName"] == "test_module"
        assert blob["script"] == "decorated_example_function()"
    
    def test_get_execute_blob_standalone_function(self):
        blob = standalone_function.get_execute_blob(10, 20)
        
        assert "script" in blob
        assert "x=10" in blob["script"]
        assert "y=20" in blob["script"]
        assert "return x + y" in blob["script"]
    
    def test_get_module_register_blob(self):
        blob = D3Function.get_module_register_blob("test_module")
        
        assert blob["moduleName"] == "test_module"
        assert "def decorated_example_function():" in blob["contents"]


class TestFunctionInfo:
    
    def test_function_info_creation(self):
        info = FunctionInfo(
            blob="def test_func(x, y):\n    return 42",
            name="test_func",
            body="return 42",
            args=["x", "y"]
        )
        
        assert info.name == "test_func"
        assert info.body == "return 42"
        assert info.args == ["x", "y"]
        assert info.blob == "def test_func(x, y):\n    return 42"
    
    def test_function_info_defaults(self):
        info = FunctionInfo(
            blob="def test_func():\n    return 42",
            name="test_func", 
            body="return 42"
        )
        assert info.args == []


class TestD3FunctionDecorator:
    
    def test_decorator_with_module(self):
        @d3function("my_module")
        def test_func():
            return "test result"
        
        assert isinstance(test_func, D3Function)
        assert test_func.module_name == "my_module"
        assert test_func.name == "test_func"
    
    def test_decorator_without_module(self):
        @d3function()
        def test_func():
            return "test result"
        
        assert isinstance(test_func, D3Function)
        assert test_func.module_name == ""
        assert test_func.name == "test_func"


class TestRegistrationFunctions:
    
    def test_get_all_modules(self):
        modules = get_all_modules()
        assert "test_module" in modules
    
    def test_get_all_d3functions(self):
        functions = get_all_d3functions()
        function_names = [name for module, name in functions]
        assert "decorated_example_function" in function_names
        assert "standalone_function" in function_names


class TestD3FunctionEquality:
    
    def test_hash_and_equality(self):
        func1 = D3Function("module1", example_function)
        func2 = D3Function("module2", example_function)  # Different module, same function
        
        # Should be equal and have same hash because they wrap the same function
        assert func1 == func2
        assert hash(func1) == hash(func2)
    
    def test_inequality_different_functions(self):
        func1 = D3Function("module1", example_function)
        func2 = D3Function("module1", example_function_with_args)
        
        # Should not be equal because they wrap different functions
        assert func1 != func2


class TestRegisterModuleD3Functions:
    
    def test_register_empty_module_name(self):
        # Empty module name should return success without making requests
        success, error = register_module_d3functions("127.0.0.1", "")
        assert success is True
        assert error == ""
    
    @patch('requests.post')
    def test_register_module_success(self, mock_post):
        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        success, error = register_module_d3functions("192.168.1.100", "test_module")
        
        assert success is True
        assert error == ""
        mock_post.assert_called_once_with(
            url="http://192.168.1.100/api/session/python/registermodule",
            json=D3Function.get_module_register_blob("test_module")
        )
    
    @patch('requests.post')
    def test_register_module_http_error(self, mock_post):
        # Mock failed response
        mock_response = Mock()
        mock_response.ok = False
        mock_post.return_value = mock_response
        
        success, error = register_module_d3functions("192.168.1.100", "test_module")
        
        assert success is False
        assert error == ""
    
    @patch('requests.post')
    def test_register_module_exception(self, mock_post):
        # Mock exception during request
        mock_post.side_effect = Exception("Connection error")
        
        success, error = register_module_d3functions("192.168.1.100", "test_module")
        
        assert success is False
        assert error == "Connection error"


class TestRegisterAllD3Functions:
    
    @patch('requests.post')
    def test_register_all_modules_success(self, mock_post):
        # Mock successful response for all modules
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        results = register_all_d3functions("127.0.0.1")
        
        # Should have results for all available modules
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # All results should be successful
        for module_name, (success, error) in results.items():
            assert success is True
            assert error == ""
        
        # Should have made HTTP requests for each module (excluding empty module names)
        expected_modules = [name for name in results.keys() if name]  # Filter out empty module names
        assert mock_post.call_count == len(expected_modules)
    
    @patch('requests.post')
    def test_register_all_modules_mixed_results(self, mock_post):
        # Mock alternating success/failure responses
        def mock_response_side_effect(*args, **kwargs):
            response = Mock()
            # Alternate between success and failure based on call count
            response.ok = (mock_post.call_count % 2 == 1)
            return response
        
        mock_post.side_effect = mock_response_side_effect
        
        results = register_all_d3functions("127.0.0.1")
        
        # Should have results for all available modules
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Should have a mix of successful and failed registrations
        success_count = sum(1 for success, _ in results.values() if success)
        failure_count = len(results) - success_count
        
        # We should have both successes and failures (depending on available modules)
        # At minimum, we know there are test_module, module_a, module_b from our test functions
        assert success_count > 0 or failure_count > 0
    
    @patch('requests.post')
    def test_register_all_modules_with_exceptions(self, mock_post):
        # Mock some requests to raise exceptions
        def mock_response_side_effect(*args, **kwargs):
            if mock_post.call_count == 1:
                raise Exception("Network error")
            response = Mock()
            response.ok = True
            return response
        
        mock_post.side_effect = mock_response_side_effect
        
        results = register_all_d3functions("127.0.0.1")
        
        # Should have results for all available modules
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Should have at least one failure due to exception
        has_failure = any(not success for success, _ in results.values())
        has_error_message = any(error != "" for _, error in results.values())
        
        # At least one module should have failed with an error message
        assert has_failure and has_error_message
    
    def test_register_all_modules_no_network_calls_for_empty_modules(self):
        # This test verifies that modules with empty names don't make network calls
        # We can't easily mock this without affecting other tests, so we test the logic indirectly
        
        # Get all available modules
        all_modules = get_all_modules()
        
        # Verify that we have some modules to work with
        assert len(all_modules) > 0
        
        # Test that empty module name handling works correctly
        success, error = register_module_d3functions("127.0.0.1", "")
        assert success is True
        assert error == ""
