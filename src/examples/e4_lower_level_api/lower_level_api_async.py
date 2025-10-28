import asyncio
import aiohttp
from d3blobgen.core import (
    register_all_d3functions,
    PluginResponse,
    D3_PLUGIN_ENDPOINT,
    D3Function,
    get_plugin_endpoint_url,
)
from d3blobgen.utils import d3_api_aplugin, d3_api_typed_aplugin
from examples.e4_lower_level_api.lower_level_api_blob import (
    my_time,
    my_time_with_note,
    will_raise_if_call_different_module_function,
    sleep_50ms,
    same_module_function_access,
    my_time_module2,
    get_surface_uid_with_time,
    get_typed_surface,
    Surface,
)


async def example_basic_blob_async():
    """Example 1: Get blob for requests (async)"""
    print("\n=== Example 1: Get blob for requests (async) ===")
    blob = my_time.get_execute_blob()
    print(f"Blob: {blob}")
    print(f"Script:\n{blob['script']}")


async def example_plugin_url_async():
    """Example 2: Get plugin URL for requests (async)"""
    print("\n=== Example 2: Get plugin URL for requests (async) ===")
    endpoint_url = get_plugin_endpoint_url("localhost", 80)
    print(f"Endpoint URL: {endpoint_url}")
    return endpoint_url


async def example_send_request_async(endpoint_url: str):
    """Example 3: Send execute blob to plugin endpoint (async)"""
    print("\n=== Example 3: Send execute blob to plugin endpoint (async) ===")
    blob = my_time.get_execute_blob()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, json=blob) as response:
                print(f"Response status: {response.status}")
                json_response = await response.json()
                print(f"JSON: {json_response}")
                return json_response
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Designer is running!")
        return None


async def example_parse_response_async(endpoint_url: str):
    """Example 4: Parse response to retrieve return value (async)"""
    print("\n=== Example 4: Parse response to retrieve return value (async) ===")
    blob = my_time_with_note.get_execute_blob("Hello Async World")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, json=blob) as response:
                json_response = await response.json()
                plugin_response = PluginResponse.model_validate(json_response)

                print(f"Response: {plugin_response}")
                print(f"Return value: {plugin_response.returnValue}")
                print(f"Return value type: {type(plugin_response.returnValue)}")
                print(f"Cast return value: {plugin_response.returnCastValue(str)}")
                print(f"Cast return value type: {type(plugin_response.returnCastValue(str))}")
    except Exception as e:
        print(f"Error: {e}")


async def example_typed_blob_async(endpoint_url: str):
    """Example 5: With typed execute blob (async)"""
    print("\n=== Example 5: With typed execute blob (async) ===")

    # Using regular blob
    blob = my_time_module2.get_execute_blob()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, json=blob) as response:
                json_response = await response.json()
                plugin_response = PluginResponse.model_validate(json_response)
                print(f"Regular blob return value: {plugin_response.returnValue}")
                print(f"Regular blob return type: {type(plugin_response.returnValue)}")
    except Exception as e:
        print(f"Error: {e}")

    # Using typed blob
    typed_blob = my_time_module2.get_typed_execute_blob()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint_url, json=typed_blob.blob) as response:
                json_response = await response.json()
                typed_plugin_response = PluginResponse[typed_blob.return_type].model_validate(json_response)
                typed_returnValue = typed_plugin_response.returnValue
                print(f"Typed blob return value: {typed_returnValue}")
                print(f"Typed blob return type: {type(typed_returnValue)}")
    except Exception as e:
        print(f"Error: {e}")


async def example_helper_utilities_async():
    """Example 6: With helper utilities (async)"""
    print("\n=== Example 6: With helper utilities (async) ===")

    try:
        # Using d3_api_aplugin
        response = await d3_api_aplugin("localhost", 80, my_time.get_execute_blob())
        returnValue = response.returnValue
        castReturnValue = response.returnCastValue(str)
        print(f"Response: {response}")
        print(f"Return value: {returnValue}")
        print(f"Return value type: {type(returnValue)}")
        print(f"Cast value: {castReturnValue}")
        print(f"Cast value type: {type(castReturnValue)}")

        # Using d3_api_typed_aplugin
        typed_response = await d3_api_typed_aplugin("localhost", 80, my_time.get_typed_execute_blob())
        typed_returnValue = typed_response.returnValue
        print(f"Typed response: {typed_response}")
        print(f"Typed return value: {typed_returnValue}")
        print(f"Typed return value type: {type(typed_returnValue)}")
    except Exception as e:
        print(f"Error: {e}")


async def example_module_functions_async():
    """Example 7: Module functions and registration (async)"""
    print("\n=== Example 7: Module functions and registration (async) ===")

    # Get typed blob from module function
    typed_blob = my_time_with_note.get_typed_execute_blob("Async example note")
    print(f"Blob: {typed_blob.blob}")

    # Get register blob for modules
    register_blob_mymodule = D3Function.get_module_register_blob("mymodule")
    print(f"\nMymodule register blob:\n{register_blob_mymodule['contents']}")

    register_blob_module2 = D3Function.get_module_register_blob("module2")
    print(f"\nModule2 register blob:\n{register_blob_module2['contents']}")


async def example_async_function_sleep():
    """Example 8: Using async function with sleep"""
    print("\n=== Example 8: Using async function with sleep (async) ===")

    try:
        response = await d3_api_typed_aplugin("localhost", 80, sleep_50ms.get_typed_execute_blob())
        print(f"Response after 50ms sleep: {response.returnValue}")
    except Exception as e:
        print(f"Error: {e}")


async def example_concurrent_requests():
    """Example 9: Concurrent async requests"""
    print("\n=== Example 9: Concurrent async requests ===")

    try:
        # Create multiple tasks to run concurrently
        tasks = [
            d3_api_typed_aplugin("localhost", 80, my_time.get_typed_execute_blob()),
            d3_api_typed_aplugin("localhost", 80, my_time_module2.get_typed_execute_blob()),
            d3_api_typed_aplugin("localhost", 80, sleep_50ms.get_typed_execute_blob()),
        ]

        # Run all tasks concurrently and wait for all to complete
        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        print(f"Completed {len(tasks)} requests concurrently in {(end_time - start_time)*1000:.2f}ms")

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Task {i+1} failed: {result}")
            else:
                print(f"Task {i+1} result: {result.returnValue}")
    except Exception as e:
        print(f"Error: {e}")


async def example_typed_dict_async():
    """Example 10: Using TypedDict return type (async)"""
    print("\n=== Example 10: Using TypedDict return type (async) ===")

    # get_surface_uid_with_time returns dict[str, str]
    typed_blob = get_surface_uid_with_time.get_typed_execute_blob("surface 1")
    print(f"Blob for get_surface_uid_with_time: {typed_blob.blob}")

    # This will only work if Designer is running with the surface available
    try:
        response = await d3_api_typed_aplugin("localhost", 80, typed_blob)
        print(f"Surface info (str uid): {response.returnValue}")
    except Exception as e:
        print(f"Error (expected if surface not available): {e}")

    # get_typed_surface returns Surface TypedDict with int uid
    typed_surface_blob = get_typed_surface.get_typed_execute_blob("surface 1")
    print(f"\nBlob for get_typed_surface: {typed_surface_blob.blob}")

    try:
        surface_response = await d3_api_typed_aplugin("localhost", 80, typed_surface_blob)
        print(f"Surface info (int uid): {surface_response.returnValue}")
    except Exception as e:
        print(f"Error (expected if surface not available): {e}")


async def example_cross_module_error_async():
    """Example 11: Cross-module function call error (async)"""
    print("\n=== Example 11: Cross-module function call error (async) ===")

    # will_raise_if_call_different_module_function is in module2
    # but tries to call my_time() which is in mymodule
    # This will raise an error because modules cannot call functions from other modules

    typed_blob = will_raise_if_call_different_module_function.get_typed_execute_blob()
    print(f"Blob: {typed_blob.blob}")
    print("Attempting to call function from different module (will fail)...")

    try:
        response = await d3_api_typed_aplugin("localhost", 80, typed_blob)
        print(f"Response: {response.returnValue}")
    except Exception as e:
        print(f"Expected error - cannot call functions across modules: {e}")


async def main_async():
    """Main async function to run all examples"""
    DESIGNER_IP = "localhost"

    # Register module functions (needed for module functions)
    register_all_d3functions(DESIGNER_IP)

    print("=" * 60)
    print("d3blobgen Lower Level API Async Examples")
    print("=" * 60)

    # Run examples that don't require Designer
    await example_basic_blob_async()
    endpoint_url = await example_plugin_url_async()
    await example_module_functions_async()

    # Examples that require Designer to be running
    print("\n" + "=" * 60)
    print("Examples requiring Designer (will show errors if not running)")
    print("=" * 60)

    await example_send_request_async(endpoint_url)
    await example_parse_response_async(endpoint_url)
    await example_typed_blob_async(endpoint_url)
    await example_helper_utilities_async()
    await example_async_function_sleep()
    await example_concurrent_requests()
    await example_typed_dict_async()
    await example_cross_module_error_async()

    print("\n" + "=" * 60)
    print("Async examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main_async())
