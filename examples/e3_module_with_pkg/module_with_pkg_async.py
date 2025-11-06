import asyncio
from d3blobgen.core import register_all_d3functions
from d3blobgen.utils import d3_api_aplugin
from examples.e3_module_with_pkg.module_with_pkg_blob import (
    my_time,
    my_time_with_note,
    will_raise_if_call_different_module_function,
    sleep_50ms,
    my_time_module2,
    get_surface_uid_with_time,
    get_typed_surface,
    Surface
)

async def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # must register all modules first
    # this will also register the packages (datetime, time) for the modules
    register_all_d3functions(DESIGNER_IP, DESIGNER_PORT)

    # execute function that uses datetime package (async)
    print("1. execute function that uses datetime package (async)")
    ret_val: str = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, my_time.blob())).returnValue
    print(f"- result: {ret_val}")

    # execute function that calls another function in same module (async)
    print("2. execute function that calls another function in same module (async)")
    ret_val = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, my_time_with_note.blob("test note"))).returnValue
    print(f"- result: {ret_val}")

    # execute function from module2 (async)
    print("3. execute function from module2 (async)")
    ret_val = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, my_time_module2.blob())).returnValue
    print(f"- result: {ret_val}")

    # execute function that uses time.sleep (async)
    print("4. execute function that uses time.sleep (async)")
    ret_val = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, sleep_50ms.blob())).returnValue
    print(f"- result: {ret_val}")

    # test exception when calling function from different module (async)
    print("5. exception when calling function from different module (async)")
    try:
        await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, will_raise_if_call_different_module_function.json())
    except Exception as e:
        print(f"- error: {e}")

    # access resource with custom data (time) (async)
    print("6. get surface uid with time (async)")
    surface_data: dict[str, str] = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid_with_time.blob(surface_name="surface 1"))).returnValue
    print(surface_data)

    # access resource with TypedDict return type (async)
    print("7. get typed surface (async)")
    typed_surface: Surface = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_typed_surface.blob(surface_name="surface 1"))).returnValue
    print(typed_surface)

if __name__ == "__main__":
    asyncio.run(main())
