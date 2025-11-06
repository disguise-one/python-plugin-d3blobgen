import asyncio
from d3blobgen.utils import d3_api_aplugin
from examples.e1_basic_interface.basic_interface_blobs import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    my_exception,
    get_surface_uid,
    rename_surface,
)


async def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # normal function call
    ret_val: int = my_add(1, 2)
    print("1. normal function call")
    print(f"- result: {ret_val}")

    # execute over Designer plugin (async)
    print("2. execute over plugin (async)")
    ret_val_from_plugin = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, my_add.blob(1, 2))).returnValue
    print(f"- result: {ret_val_from_plugin}")

    print("3. custom timeout 2ms (async)")
    try:
        ret_str: str = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_2ms.blob(), timeout_sec=0.002)).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. custom timeout 1sec (async)")
    try:
        ret_str: str = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_1sec.blob(), timeout_sec=1)).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("5. exception over execute (async)")
    try:
        await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, my_exception.json())
    except Exception as e:
        print(e)

    # access resource in Designer
    print("6. get surface uid (async)")
    surface_uid: dict[str, str] = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 1"))).returnValue
    print(surface_uid)

    # update resource in Designer
    print("7. rename surface (async)")
    await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.json(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 2"))).returnValue
    print(surface_uid)
    await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.json(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = (await d3_api_aplugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 1"))).returnValue
    print(surface_uid)

if __name__ == "__main__":
    asyncio.run(main())
