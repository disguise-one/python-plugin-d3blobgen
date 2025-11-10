"""
d3blobgen Low Level API Examples (Synchronous)

This module demonstrates the synchronous low-level interface for d3blobgen, showing how to:
1. Create blobs for requests (local operations, Designer not needed)
2. Register modules with Designer (requires Designer running)
3. Execute functions via the plugin endpoint (requires Designer running)
4. Handle exceptions (requires Designer running)

Note: Designer must be running for any plugin execution (examples 2-4).

For async examples, see lower_level_api_async.py
"""

import requests
from d3blobgen.core import d3function, D3Function, TypedBlob
from d3blobgen.models import PluginResponse, PluginException
from d3blobgen.api import (
    get_plugin_module_register_url,
    get_plugin_endpoint_url,
    d3_api_plugin_raw,
    d3_api_plugin,
)


def example_blob_without_module():
    """Example 1: Get blob for requests (without module)"""
    print("\n" + "=" * 60)
    print("Example 1: Get blob for requests (without module)")
    print("=" * 60)

    @d3function
    def my_add(a: int, b: int) -> int:
        return a + b

    blob: TypedBlob[int] = my_add.blob(1, 2)
    print(f"blob: {blob}")
    print(f"\nScript:\n{blob.json['script']}")


def example_blob_with_module():
    """Example 2: Get blob for requests (with module)"""
    print("\n" + "=" * 60)
    print("Example 2: Get blob for requests (with module)")
    print("=" * 60)

    @d3function(module_name="mymodule")
    def my_add(a: int, b: int) -> int:
        return a + b

    blob: TypedBlob[int] = my_add.blob(1, 2)
    print(f"blob: {blob}")
    print(f"\nScript:\n{blob.json['script']}")

    return my_add


def example_register_module(designer_ip: str, designer_port: int):
    """Example 3: Registering d3function module"""
    print("\n" + "=" * 60)
    print("Example 3: Registering d3function module")
    print("=" * 60)

    @d3function(module_name="mymodule")
    def my_add(a: int, b: int) -> int:
        return a + b

    register_url: str = get_plugin_module_register_url(designer_ip, designer_port)
    json_data: dict[str, str] | None = D3Function.get_module_register_json("mymodule")
    print("json:")
    print(json_data)

    try:
        response = requests.post(register_url, json=json_data)
        print("\nresponse:")
        print(response.text)
        return my_add
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Designer is running!")
        return None


def example_execute_raw_json(designer_ip: str, designer_port: int, my_add):
    """Example 4: Execute with raw json (no type information)"""
    print("\n" + "=" * 60)
    print("Example 4: Execute with raw json (no type information)")
    print("=" * 60)

    json_data = my_add.json(1, 2)
    print("json:")
    print(json_data)

    try:
        # Using d3_api_plugin_raw
        response: PluginResponse = d3_api_plugin_raw(designer_ip, designer_port, json_data)
        print("\nresponse:")
        print(response)
        print("\nreturnValue:")
        print(response.returnValue)

        print("\nreturnValue with type check:")
        returnValue: int = response.returnCastValue(int)
        print(f"type: {type(returnValue)}")
        print(f"value: {returnValue}")

        # Using requests directly
        plugin_url: str = get_plugin_endpoint_url(designer_ip, designer_port)
        print(f"\nplugin_url: {plugin_url}")
        requests_response = requests.post(plugin_url, json=json_data)
        print("response:")
        print(requests_response.text)
        print("returnValue:")
        print(requests_response.json().get("returnValue"))
    except Exception as e:
        print(f"Error: {e}")


def example_execute_typed_blob(designer_ip: str, designer_port: int, my_add):
    """Example 5: Execute with blob (type information)"""
    print("\n" + "=" * 60)
    print("Example 5: Execute with blob (type information)")
    print("=" * 60)

    blob: TypedBlob[int] = my_add.blob(1, 2)
    print("blob:")
    print(blob)

    try:
        response: PluginResponse[int] = d3_api_plugin(designer_ip, designer_port, blob)
        print("\nresponse:")
        print(response)
        print("\nreturnValue:")
        print(response.returnValue)
    except Exception as e:
        print(f"Error: {e}")


def example_exception_handling(designer_ip: str, designer_port: int):
    """Example 6: Exception handling"""
    print("\n" + "=" * 60)
    print("Example 6: Exception handling")
    print("=" * 60)

    @d3function
    def my_exception_handling():
        raise RuntimeError("This is my exception!")

    blob: TypedBlob = my_exception_handling.blob()
    print("blob:")
    print(blob)

    try:
        response: PluginResponse[int] = d3_api_plugin(designer_ip, designer_port, blob)
        print("response:")
        print(response)
    except PluginException as e:
        print("\nCaught PluginException:")
        print(e)


def main():
    """Run all examples"""
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    print("=" * 60)
    print("d3blobgen Low Level API Examples (Sync)")
    print("=" * 60)

    # Blob generation examples (local only, Designer not needed)
    print("\n" + "=" * 60)
    print("Blob Generation (Designer not required)")
    print("=" * 60)

    example_blob_without_module()
    my_add = example_blob_with_module()

    # Execution examples (Designer MUST be running)
    print("\n" + "=" * 60)
    print("Plugin Execution (Designer MUST be running)")
    print("=" * 60)

    my_add = example_register_module(DESIGNER_IP, DESIGNER_PORT)
    if my_add:
        example_execute_raw_json(DESIGNER_IP, DESIGNER_PORT, my_add)
        example_execute_typed_blob(DESIGNER_IP, DESIGNER_PORT, my_add)
        example_exception_handling(DESIGNER_IP, DESIGNER_PORT)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
