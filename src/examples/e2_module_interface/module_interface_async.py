import asyncio
from d3blobgen.core import register_all_d3functions, register_module_d3functions
from examples.e2_module_interface.module_interface_blob import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    use_my_add,
    get_surface_uid,
    rename_surface,
)

async def main():
    # must register module first
    register_all_d3functions("localhost")

    # you can register specific module as well
    # register_module_d3functions("localhost", "mymodule")

    # execute over Designer plugin (async)
    print("1. execute over plugin (async)")
    ret_val = await my_add.aexecute(1, 2)
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms (async)")
    try:
        ret_str: str = await custom_timeout_2ms.aexecute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec (async)")
    try:
        ret_str: str = await custom_timeout_1sec.aexecute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("4. execute function that calls the other function (async)")
    ret_val = await use_my_add.aexecute(1, 2)
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid (async)")
    surface_uid: dict[str, str] = await get_surface_uid.aexecute(surface_name="surface 1")
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface (async)")
    await rename_surface.aexecute(surface_name="surface 1", new_surface_name="surface 2")
    surface_uid = await get_surface_uid.aexecute(surface_name="surface 2")
    print(surface_uid)
    await rename_surface.aexecute(surface_name="surface 2", new_surface_name="surface 1")
    surface_uid = await get_surface_uid.aexecute(surface_name="surface 1")
    print(surface_uid)

if __name__ == "__main__":
    asyncio.run(main())
