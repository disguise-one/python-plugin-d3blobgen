import requests
from d3blobgen.core import (
    register_all_d3functions,
    D3Function,
)
from d3blobgen.models import (
    PluginResponse,
    D3_PLUGIN_ENDPOINT,
)
from d3blobgen.utils import d3_api_plugin, get_plugin_endpoint_url
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


def example_basic_blob():
    """Example 1: Get blob for requests"""
    print("\n=== Example 1: Get blob for requests ===")
    blob = my_time.json()
    print(f"Blob: {blob}")
    print(f"Script:\n{blob['script']}")


def example_plugin_url():
    """Example 2: Get plugin URL for requests"""
    print("\n=== Example 2: Get plugin URL for requests ===")
    endpoint_url = get_plugin_endpoint_url("localhost", 80)
    print(f"Endpoint URL: {endpoint_url}")
    return endpoint_url


def example_send_request(endpoint_url: str):
    """Example 3: Send execute blob to plugin endpoint"""
    print("\n=== Example 3: Send execute blob to plugin endpoint ===")
    blob = my_time.json()

    try:
        response = requests.post(endpoint_url, json=blob)
        print(f"Response: {response}")
        print(f"JSON: {response.json()}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Designer is running!")
        return None


def example_parse_response(endpoint_url: str):
    """Example 4: Parse response to retrieve return value"""
    print("\n=== Example 4: Parse response to retrieve return value ===")
    blob = my_time_with_note.json("Hello World")

    try:
        response = requests.post(endpoint_url, json=blob)
        plugin_response = PluginResponse.model_validate(response.json())

        print(f"Response: {plugin_response}")
        print(f"Return value: {plugin_response.returnValue}")
        print(f"Return value type: {type(plugin_response.returnValue)}")
        print(f"Cast return value: {plugin_response.returnCastValue(str)}")
        print(f"Cast return value type: {type(plugin_response.returnCastValue(str))}")
    except Exception as e:
        print(f"Error: {e}")


def example_typed_blob(endpoint_url: str):
    """Example 5: With typed execute blob"""
    print("\n=== Example 5: With typed execute blob ===")

    # Using regular blob
    blob = my_time_module2.json()
    try:
        response = requests.post(endpoint_url, json=blob)
        plugin_response = PluginResponse.model_validate(response.json())
        print(f"Regular blob return value: {plugin_response.returnValue}")
        print(f"Regular blob return type: {type(plugin_response.returnValue)}")
    except Exception as e:
        print(f"Error: {e}")

    # Using typed blob
    typed_blob = my_time_module2.blob()
    try:
        response = requests.post(endpoint_url, json=typed_blob.json)
        typed_plugin_response = PluginResponse[typed_blob.return_type].model_validate(response.json())
        typed_returnValue = typed_plugin_response.returnValue
        print(f"Typed blob return value: {typed_returnValue}")
        print(f"Typed blob return type: {type(typed_returnValue)}")
    except Exception as e:
        print(f"Error: {e}")


def example_helper_utilities():
    """Example 6: With helper utilities"""
    print("\n=== Example 6: With helper utilities ===")

    # Using d3_api_plugin
    response = d3_api_plugin("localhost", 80, my_time.json())
    returnValue = response.returnValue
    castReturnValue = response.returnCastValue(str)
    print(f"Response: {response}")
    print(f"Return value: {returnValue}")
    print(f"Return value type: {type(returnValue)}")
    print(f"Cast value: {castReturnValue}")
    print(f"Cast value type: {type(castReturnValue)}")

    # Using d3_api_plugin
    typed_response = d3_api_plugin("localhost", 80, my_time.blob())
    typed_returnValue = typed_response.returnValue
    print(f"Typed response: {typed_response}")
    print(f"Typed return value: {typed_returnValue}")
    print(f"Typed return value type: {type(typed_returnValue)}")


def example_module_functions():
    """Example 7: Module functions and registration"""
    print("\n=== Example 7: Module functions and registration ===")

    # Get typed blob from module function
    typed_blob = my_time_with_note.blob("Example note")
    print(f"Blob: {typed_blob.json}")

    # Get register blob for modules
    register_blob_mymodule = D3Function.get_module_register_blob("mymodule")
    print(f"\nMymodule register blob:\n{register_blob_mymodule['contents']}")

    register_blob_module2 = D3Function.get_module_register_blob("module2")
    print(f"\nModule2 register blob:\n{register_blob_module2['contents']}")


def example_async_function():
    """Example 8: Using async function with sleep"""
    print("\n=== Example 8: Using async function with sleep ===")

    try:
        response = d3_api_plugin("localhost", 80, sleep_50ms.blob())
        print(f"Response after 50ms sleep: {response.returnValue}")
    except Exception as e:
        print(f"Error: {e}")


def example_same_module_function_access():
    """Example 10: Same module function access"""
    print("\n=== Example 10: Same module function access ===")

    # same_module_function_access calls sleep_50ms (both in module2)
    # Note: same_module_function_access is NOT decorated with @d3function
    # so we need to call it through a d3function
    print("Demonstrating same module function access:")
    print("same_module_function_access() calls sleep_50ms() within module2")

    try:
        # This function is not a d3function, so it can't be called directly via blob
        # It's meant to show that functions in the same module can call each other
        result = same_module_function_access("Testing same module access")
        print(f"Direct call result: {result}")
    except Exception as e:
        print(f"Error: {e}")


def example_cross_module_error():
    """Example 11: Cross-module function call error"""
    print("\n=== Example 11: Cross-module function call error ===")

    # will_raise_if_call_different_module_function is in module2
    # but tries to call my_time() which is in mymodule
    # This will raise an error because modules cannot call functions from other modules

    typed_blob = will_raise_if_call_different_module_function.blob()
    print(f"Blob: {typed_blob.json}")
    print("Attempting to call function from different module (will fail)...")

    try:
        response = d3_api_plugin("localhost", 80, typed_blob)
        print(f"Response: {response.returnValue}")
    except Exception as e:
        print(f"Expected error - cannot call functions across modules: {e}")


def example_typed_dict():
    """Example 9: Using TypedDict return type"""
    print("\n=== Example 9: Using TypedDict return type ===")

    # get_surface_uid_with_time returns dict[str, str]
    typed_blob = get_surface_uid_with_time.blob("surface 1")
    print(f"Blob for get_surface_uid_with_time: {typed_blob.json}")

    # This will only work if Designer is running with the surface available
    try:
        response = d3_api_plugin("localhost", 80, typed_blob)
        print(f"Surface info (str uid): {response.returnValue}")
    except Exception as e:
        print(f"Error (expected if surface not available): {e}")

    # get_typed_surface returns Surface TypedDict with int uid
    typed_surface_blob = get_typed_surface.blob("surface 1")
    print(f"\nBlob for get_typed_surface: {typed_surface_blob.json}")

    try:
        surface_response = d3_api_plugin("localhost", 80, typed_surface_blob)
        print(f"Surface info (int uid): {surface_response.returnValue}")
    except Exception as e:
        print(f"Error (expected if surface not available): {e}")


def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # Register module functions (needed for module functions)
    register_all_d3functions(DESIGNER_IP, DESIGNER_PORT)

    print("=" * 60)
    print("d3blobgen Lower Level API Examples")
    print("=" * 60)

    # Run examples that don't require Designer
    example_basic_blob()
    endpoint_url = example_plugin_url()
    example_module_functions()

    # Examples that require Designer to be running
    print("\n" + "=" * 60)
    print("Examples requiring Designer (will show errors if not running)")
    print("=" * 60)

    example_send_request(endpoint_url)
    example_parse_response(endpoint_url)
    example_typed_blob(endpoint_url)
    example_helper_utilities()
    example_async_function()
    example_typed_dict()
    example_same_module_function_access()
    example_cross_module_error()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
