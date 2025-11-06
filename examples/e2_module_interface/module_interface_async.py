import asyncio
from d3blobgen.core import register_all_d3functions
from d3blobgen.utils import d3_api_aplugin
from examples.e2_module_interface.module_interface_blob import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    use_my_add,
    get_surface_uid,
    rename_surface,
)

async def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # must register module first
    register_all_d3functions(DESIGNER_IP, DESIGNER_PORT)

    # execute over Designer plugin (async)
    print("1. execute over plugin (async)")
    ret_val = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, my_add.blob(1, 2))).returnValue
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms (async)")
    try:
        ret_str: str = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_2ms.blob(), timeout_sec=0.002)).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec (async)")
    try:
        ret_str: str = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_1sec.blob(), timeout_sec=1)).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("4. execute function that calls the other function (async)")
    ret_val = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, use_my_add.blob(1, 2))).returnValue
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid (async)")
    surface_uid: dict[str, str] = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 1"))).returnValue
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface (async)")
    await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.json(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 2"))).returnValue
    print(surface_uid)
    await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.json(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 1"))).returnValue
    print(surface_uid)

if __name__ == "__main__":
    asyncio.run(main())
