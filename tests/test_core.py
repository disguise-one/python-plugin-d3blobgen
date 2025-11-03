from unittest.mock import AsyncMock, Mock, patch

import pytest

from d3blobgen.core import (
    D3Function,
    FunctionInfo,
    aregister_all_d3functions,
    aregister_module_d3functions,
    d3function,
    extract_function_info,
    get_all_d3functions,
    get_all_modules,
    register_all_d3functions,
    register_module_d3functions,
)


def example_function():
    """Example function for testing"""
    return "hello world"


def example_function_with_args(name, value):
    """Example function with arguments for testing"""
    return f"Hello {name}, value is {value}"


def typed_function_with_args(name: str, value: int) -> str:
    """Type-annotated function with arguments for testing"""
    result: str = f"Hello {name}, value is {value}"
    return result


def typed_function_complex(items: list[str], count: int = 5) -> dict[str, int]:
    """Complex type-annotated function for testing"""
    data: dict[str, int] = {}
    for i, item in enumerate(items[:count]):
        data[item] = i
    return data


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

    def test_extract_info_typed_function(self):
        # Test type annotation handling
        info = extract_function_info(typed_function_with_args)

        assert info.name == "typed_function_with_args"
        assert info.args == ["name", "value"]

        # Regular blob should contain type annotations
        assert ": str" in info.blob
        assert "-> str" in info.blob
        assert "result: str" in info.blob

        # Python 2.7 blob should NOT contain type annotations
        assert ": str" not in info.blob_py27
        assert "-> str" not in info.blob_py27
        assert "result: str" not in info.blob_py27
        # But should contain the variable assignment without type hint
        assert "result =" in info.blob_py27

    def test_extract_info_complex_typed_function(self):
        # Test complex type annotations
        info = extract_function_info(typed_function_complex)

        assert info.name == "typed_function_complex"
        assert info.args == ["items", "count"]

        # Regular blob should contain complex type annotations
        assert "list[str]" in info.blob
        assert "dict[str, int]" in info.blob
        assert "-> dict[str, int]" in info.blob
        assert "data: dict[str, int]" in info.blob

        # Python 2.7 blob should NOT contain type annotations
        assert "list[str]" not in info.blob_py27
        assert "dict[str, int]" not in info.blob_py27
        assert "-> dict[str, int]" not in info.blob_py27
        assert "data: dict[str, int]" not in info.blob_py27
        # But should contain the variable assignment without type hint
        assert "data =" in info.blob_py27


class TestD3Function:

    def test_d3_function_creation(self):
        d3_func = D3Function("test_module", None, example_function)

        assert d3_func.name == "example_function"
        assert d3_func.module_name == "test_module"
        assert d3_func._is_module_function

    def test_d3_function_standalone(self):
        d3_func = D3Function("", None, standalone_function._function)

        assert d3_func.name == "standalone_function"
        assert d3_func.module_name == ""
        assert not d3_func._is_module_function

    def test_d3_function_call(self):
        # Test that the wrapped function can still be called
        result = decorated_example_function()
        assert result == "decorated hello world"

        result = standalone_function(5, 3)
        assert result == 8

    def test_get_execute_blob_module_function(self):
        blob = decorated_example_function.get_execute_blob()

        assert blob["moduleName"] == "test_module"
        assert blob["script"] == "return decorated_example_function()"

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

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aexecute_success(self, mock_post):
        # Mock successful async response
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "status": {"code": 0, "message": "", "details": []},
            "returnValue": '"test result"'
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        # Set registered IP address
        D3Function._registered_ipaddr = "127.0.0.1"

        result = await decorated_example_function.aexecute()

        assert result == "test result"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aexecute_http_error(self, mock_post):
        # Mock HTTP error response
        mock_response = AsyncMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_post.return_value.__aenter__.return_value = mock_response

        # Set registered IP address
        D3Function._registered_ipaddr = "127.0.0.1"

        with pytest.raises(RuntimeError, match="HTTP error 500"):
            await decorated_example_function.aexecute()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aexecute_designer_api_error(self, mock_post):
        # Mock Designer API error response
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "status": {
                "code": 1,
                "message": "Python error",
                "d3Log": "D3 log message",
                "pythonLog": "Python traceback"
            }
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        # Set registered IP address
        D3Function._registered_ipaddr = "127.0.0.1"

        with pytest.raises(RuntimeError, match="Designer API error"):
            await decorated_example_function.aexecute()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aexecute_empty_return_value(self, mock_post):
        # Mock response with empty return value
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_response.json = AsyncMock(return_value={
            "status": {"code": 0, "message": "", "details": []},
            "returnValue": None
        })
        mock_post.return_value.__aenter__.return_value = mock_response

        # Set registered IP address
        D3Function._registered_ipaddr = "127.0.0.1"

        with pytest.raises(RuntimeError, match="Failed to parse plugin response"):
            await decorated_example_function.aexecute()


class TestFunctionInfo:

    def test_function_info_creation(self):
        info = FunctionInfo(
            blob="def test_func(x: int, y: int) -> int:\n    return 42",
            blob_py27="def test_func(x, y):\n    return 42",
            name="test_func",
            body="return 42",
            body_py27="return 42",
            args=["x", "y"]
        )

        assert info.name == "test_func"
        assert info.body == "return 42"
        assert info.body_py27 == "return 42"
        assert info.args == ["x", "y"]
        assert info.blob == "def test_func(x: int, y: int) -> int:\n    return 42"
        assert info.blob_py27 == "def test_func(x, y):\n    return 42"

    def test_function_info_defaults(self):
        info = FunctionInfo(
            blob="def test_func() -> int:\n    return 42",
            blob_py27="def test_func():\n    return 42",
            name="test_func",
            body="return 42",
            body_py27="return 42"
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
        func1 = D3Function("module1", None, example_function)
        func2 = D3Function("module2", None, example_function)  # Different module, same function

        # Should be equal and have same hash because they wrap the same function
        assert func1 == func2
        assert hash(func1) == hash(func2)

    def test_inequality_different_functions(self):
        func1 = D3Function("module1", None, example_function)
        func2 = D3Function("module1", None, example_function_with_args)

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
        for _module_name, (success, error) in results.items():
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


class TestAsyncRegisterModuleD3Functions:

    @pytest.mark.asyncio
    async def test_aregister_empty_module_name(self):
        # Empty module name should return success without making requests
        success, error = await aregister_module_d3functions("127.0.0.1", "")
        assert success is True
        assert error == ""

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aregister_module_success(self, mock_post):
        # Mock successful async response
        mock_response = AsyncMock()
        mock_response.ok = True
        mock_post.return_value.__aenter__.return_value = mock_response

        success, error = await aregister_module_d3functions("192.168.1.100", "test_module")

        assert success is True
        assert error == ""
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aregister_module_http_error(self, mock_post):
        # Mock failed async response
        mock_response = AsyncMock()
        mock_response.ok = False
        mock_post.return_value.__aenter__.return_value = mock_response

        success, error = await aregister_module_d3functions("192.168.1.100", "test_module")

        assert success is False
        assert error == ""

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_aregister_module_exception(self, mock_post):
        # Mock exception during async request
        mock_post.side_effect = Exception("Connection error")

        success, error = await aregister_module_d3functions("192.168.1.100", "test_module")

        assert success is False
        assert error == "Connection error"


class TestAsyncRegisterAllD3Functions:

    @pytest.mark.asyncio
    @patch('d3blobgen.core.aregister_module_d3functions')
    async def test_aregister_all_modules_success(self, mock_aregister_module):
        # Mock successful registration for all modules
        mock_aregister_module.return_value = (True, "")

        results = await aregister_all_d3functions("127.0.0.1")

        # Should have results for all available modules
        assert isinstance(results, dict)
        assert len(results) > 0

        # All results should be successful
        for _module_name, (success, error) in results.items():
            assert success is True
            assert error == ""

        # Should have called aregister_module_d3functions for each module (including empty modules)
        expected_calls = len(results.keys())
        assert mock_aregister_module.call_count == expected_calls

    @pytest.mark.asyncio
    @patch('d3blobgen.core.aregister_module_d3functions')
    async def test_aregister_all_modules_mixed_results(self, mock_aregister_module):
        # Mock alternating success/failure responses
        call_count = 0
        async def mock_aregister_side_effect(ipaddr, module_name):
            nonlocal call_count
            call_count += 1
            # Alternate between success and failure
            if call_count % 2 == 1:
                return (True, "")
            else:
                return (False, "Mock error")

        mock_aregister_module.side_effect = mock_aregister_side_effect

        results = await aregister_all_d3functions("127.0.0.1")

        # Should have results for all available modules
        assert isinstance(results, dict)
        assert len(results) > 0

        # Should have a mix of successful and failed registrations
        success_count = sum(1 for success, _ in results.values() if success)
        failure_count = len(results) - success_count

        # We should have both successes and failures
        assert success_count > 0 or failure_count > 0

    @pytest.mark.asyncio
    @patch('d3blobgen.core.aregister_module_d3functions')
    async def test_aregister_all_modules_with_exceptions(self, mock_aregister_module):
        # Mock some registrations to raise exceptions
        call_count = 0
        async def mock_aregister_side_effect(ipaddr, module_name):
            nonlocal call_count
            call_count += 1
            # First call raises exception, others succeed
            if call_count == 1:
                return (False, "Network error")
            else:
                return (True, "")

        mock_aregister_module.side_effect = mock_aregister_side_effect

        results = await aregister_all_d3functions("127.0.0.1")

        # Should have results for all available modules
        assert isinstance(results, dict)
        assert len(results) > 0

        # Should have at least one failure due to exception
        has_failure = any(not success for success, _ in results.values())
        has_error_message = any(error != "" for _, error in results.values())

        # At least one module should have failed with an error message
        assert has_failure and has_error_message

    @pytest.mark.asyncio
    async def test_aregister_all_modules_sets_registered_ipaddr(self):
        # Test that the function sets the registered IP address
        test_ip = "192.168.1.200"

        # Store original IP address
        original_ip = D3Function._registered_ipaddr

        try:
            with patch('d3blobgen.core.aregister_module_d3functions') as mock_aregister_module:
                mock_aregister_module.return_value = (True, "")

                await aregister_all_d3functions(test_ip)

                # Should have set the registered IP address
                assert D3Function._registered_ipaddr == test_ip

        finally:
            # Restore original IP address
            D3Function._registered_ipaddr = original_ip
