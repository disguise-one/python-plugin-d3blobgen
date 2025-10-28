import asyncio
from examples.e1_basic_interface.basic_interface_blobs import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    my_exception,
    get_surface_uid,
    rename_surface,
)


async def main():
    # normal function call
    ret_val: int = my_add(1, 2)
    print("1. normal function call")
    print(f"- result: {ret_val}")

    # execute over Designer plugin (async)
    print("2. execute over plugin (async)")
    ret_val_from_plugin = await my_add.aexecute(1, 2)
    print(f"- result: {ret_val_from_plugin}")

    print("3. custom timeout 2ms (async)")
    try:
        ret_str: str = await custom_timeout_2ms.aexecute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. custom timeout 1sec (async)")
    try:
        ret_str: str = await custom_timeout_1sec.aexecute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("5. exception over execute (async)")
    try:
        await my_exception.aexecute()
    except Exception as e:
        print(e)

    # access resource in Designer
    print("6. get surface uid (async)")
    surface_uid: dict[str, str] = await get_surface_uid.aexecute(surface_name="surface 1")
    print(surface_uid)

    # update resource in Designer
    print("7. rename surface (async)")
    await rename_surface.aexecute(surface_name="surface 1", new_surface_name="surface 2")
    surface_uid = await get_surface_uid.aexecute(surface_name="surface 2")
    print(surface_uid)
    await rename_surface.aexecute(surface_name="surface 2", new_surface_name="surface 1")
    surface_uid = await get_surface_uid.aexecute(surface_name="surface 1")
    print(surface_uid)

if __name__ == "__main__":
    asyncio.run(main())
