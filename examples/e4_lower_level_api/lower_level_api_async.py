"""
d3blobgen Low Level API Examples (Asynchronous)

This module demonstrates the asynchronous low-level interface for d3blobgen, showing how to:
1. Create blobs for requests
2. Register modules with Designer (async)
3. Execute functions via the plugin endpoint (async)
4. Handle exceptions (async)
5. Run concurrent requests

For sync examples, see lower_level_api.py
"""

import asyncio
import aiohttp
from d3blobgen.core import d3function, D3Function, TypedBlob
from d3blobgen.models import PluginResponse, PluginException
from d3blobgen.api import (
    get_plugin_module_register_url,
    get_plugin_endpoint_url,
    d3_api_aregister_module,
    d3_api_aplugin_raw,
    d3_api_aplugin,
)


async def example_blob_without_module():
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


async def example_blob_with_module():
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


async def example_register_module(designer_ip: str, designer_port: int):
    """Example 3: Registering d3function module (async)"""
    print("\n" + "=" * 60)
    print("Example 3: Registering d3function module (async)")
    print("=" * 60)

    @d3function(module_name="mymodule")
    def my_add(a: int, b: int) -> int:
        return a + b

    json_data: dict[str, str] | None = D3Function.get_module_register_json("mymodule")
    print("json:")
    print(json_data)

    try:
        response = await d3_api_aregister_module(designer_ip, designer_port, json_data)
        print("\nresponse:")
        print(response)
        return my_add
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Designer is running!")
        return None


async def example_execute_raw_json(designer_ip: str, designer_port: int, my_add):
    """Example 4: Execute with raw json (no type information) - async"""
    print("\n" + "=" * 60)
    print("Example 4: Execute with raw json (no type information) - async")
    print("=" * 60)

    json_data = my_add.json(1, 2)
    print("json:")
    print(json_data)

    try:
        # Using d3_api_aplugin_raw
        response: PluginResponse = await d3_api_aplugin_raw(designer_ip, designer_port, json_data)
        print("\nresponse:")
        print(response)
        print("\nreturnValue:")
        print(response.returnValue)

        print("\nreturnValue with type check:")
        returnValue: int = response.returnCastValue(int)
        print(f"type: {type(returnValue)}")
        print(f"value: {returnValue}")

        # Using aiohttp directly
        plugin_url: str = get_plugin_endpoint_url(designer_ip, designer_port)
        print(f"\nplugin_url: {plugin_url}")
        async with aiohttp.ClientSession() as session:
            async with session.post(plugin_url, json=json_data) as aiohttp_response:
                response_text = await aiohttp_response.text()
                response_json = await aiohttp_response.json()
                print("response:")
                print(response_text)
                print("returnValue:")
                print(response_json.get("returnValue"))
    except Exception as e:
        print(f"Error: {e}")


async def example_execute_typed_blob(designer_ip: str, designer_port: int, my_add):
    """Example 5: Execute with blob (type information) - async"""
    print("\n" + "=" * 60)
    print("Example 5: Execute with blob (type information) - async")
    print("=" * 60)

    blob: TypedBlob[int] = my_add.blob(1, 2)
    print("blob:")
    print(blob)

    try:
        response: PluginResponse[int] = await d3_api_aplugin(designer_ip, designer_port, blob)
        print("\nresponse:")
        print(response)
        print("\nreturnValue:")
        print(response.returnValue)
    except Exception as e:
        print(f"Error: {e}")


async def example_exception_handling(designer_ip: str, designer_port: int):
    """Example 6: Exception handling - async"""
    print("\n" + "=" * 60)
    print("Example 6: Exception handling - async")
    print("=" * 60)

    @d3function
    def my_exception_handling():
        raise RuntimeError("This is my exception!")

    blob: TypedBlob = my_exception_handling.blob()
    print("blob:")
    print(blob)

    try:
        response: PluginResponse[int] = await d3_api_aplugin(designer_ip, designer_port, blob)
        print("response:")
        print(response)
    except PluginException as e:
        print("\nCaught PluginException:")
        print(e)


async def example_concurrent_requests(designer_ip: str, designer_port: int):
    """Example 7: Concurrent async requests"""
    print("\n" + "=" * 60)
    print("Example 7: Concurrent async requests")
    print("=" * 60)

    @d3function(module_name="mymodule")
    def add_1_2(a: int, b: int) -> int:
        return a + b

    @d3function(module_name="mymodule")
    def add_3_4(a: int, b: int) -> int:
        return a + b

    @d3function(module_name="mymodule")
    def add_5_6(a: int, b: int) -> int:
        return a + b

    try:
        # Create multiple tasks to run concurrently
        tasks = [
            d3_api_aplugin(designer_ip, designer_port, add_1_2.blob(1, 2)),
            d3_api_aplugin(designer_ip, designer_port, add_3_4.blob(3, 4)),
            d3_api_aplugin(designer_ip, designer_port, add_5_6.blob(5, 6)),
        ]

        # Run all tasks concurrently and wait for all to complete
        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        print(f"Completed {len(tasks)} requests concurrently in {(end_time - start_time)*1000:.2f}ms")

        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                print(f"Task {i+1} failed: {result}")
            else:
                print(f"Task {i+1} result: {result.returnValue}")
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all async examples"""
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    print("=" * 60)
    print("d3blobgen Low Level API Examples (Async)")
    print("=" * 60)

    # Examples that don't require Designer
    print("\n" + "=" * 60)
    print("Examples without Designer connection")
    print("=" * 60)

    await example_blob_without_module()
    my_add = await example_blob_with_module()

    # Examples that require Designer
    print("\n" + "=" * 60)
    print("Examples requiring Designer connection")
    print("=" * 60)

    my_add = await example_register_module(DESIGNER_IP, DESIGNER_PORT)
    if my_add:
        await example_execute_raw_json(DESIGNER_IP, DESIGNER_PORT, my_add)
        await example_execute_typed_blob(DESIGNER_IP, DESIGNER_PORT, my_add)
        await example_exception_handling(DESIGNER_IP, DESIGNER_PORT)
        await example_concurrent_requests(DESIGNER_IP, DESIGNER_PORT)

    print("\n" + "=" * 60)
    print("Async examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
