import asyncio
from d3blobgen.session import D3AsyncSession
from e3_d3function_module_interface.module_interface_blob import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    use_my_add,
    get_surface_uid,
    rename_surface,
    my_time,
    my_time_with_note,
    sleep_50ms,
    my_time_module2,
    get_surface_uid_with_time,
    get_typed_surface,
)

DESIGNER_IP = "localhost"
DESIGNER_PORT = 80

async def with_context():
    async with D3AsyncSession(DESIGNER_IP, DESIGNER_PORT, ["mymodule", "module2"]) as session:
        # mymodule will be register by context __aenter__
        print("1. execute over plugin (async)")
        ret_val: int = await session.rpc(my_add.blob(1, 2))
        print(f"- result: {ret_val}")

        print("2. custom timeout 2ms (async)")
        try:
            ret_str: str = await session.rpc(custom_timeout_2ms.blob(), timeout_sec=0.002)
            print(f"- result: {ret_str}")
        except Exception as e:
            print(e)

        print("3. custom timeout 1sec (async)")
        try:
            ret_str: str = await session.rpc(custom_timeout_1sec.blob(), timeout_sec=1)
            print(f"- result: {ret_str}")
        except Exception as e:
            print(e)

        print("4. execute function that calls the other function (async)")
        ret_val = await session.rpc(use_my_add.blob(1, 2))
        print(f"- result: {ret_val}")

        # access resource in Designer
        print("5. get surface uid (async)")
        surface_uid: dict[str, str] = await session.rpc(get_surface_uid.blob(surface_name="surface 1"))
        print(surface_uid)

        # update resource in Designer
        print("6. rename surface (async)")
        await session.rpc(rename_surface.blob(surface_name="surface 1", new_surface_name="surface 2"))
        surface_uid = await session.rpc(get_surface_uid.blob(surface_name="surface 2"))
        print(surface_uid)
        await session.rpc(rename_surface.blob(surface_name="surface 2", new_surface_name="surface 1"))
        surface_uid = await session.rpc(get_surface_uid.blob(surface_name="surface 1"))
        print(surface_uid)

        # time-related functions
        print("7. get current time (mymodule) (async)")
        current_time: str = await session.rpc(my_time.blob())
        print(f"- result: {current_time}")

        print("8. get current time with note (mymodule) (async)")
        time_with_note: str = await session.rpc(my_time_with_note.blob(note="test note"))
        print(f"- result: {time_with_note}")

        # module2 functions
        print("9. sleep 50ms (module2) (async)")
        result: str = await session.rpc(sleep_50ms.blob())
        print(f"- result: {result}")

        print("10. get current time (module2) (async)")
        time_module2: str = await session.rpc(my_time_module2.blob())
        print(f"- result: {time_module2}")

        print("11. get surface uid with time (module2) (async)")
        surface_with_time: dict[str, str] = await session.rpc(get_surface_uid_with_time.blob(surface_name="surface 1"))
        print(surface_with_time)

        print("12. get typed surface (module2) (async)")
        typed_surface = await session.rpc(get_typed_surface.blob(surface_name="surface 1"))
        print(typed_surface)


async def without_context():
    # init session to communicate with d3
    session = D3AsyncSession(DESIGNER_IP, DESIGNER_PORT)

    # register all d3function modules
    respond: dict[str, bool] = await session.register_all_modules()
    print(f"register module result: {respond}")

    print("1. execute over plugin (async)")
    ret_val: int = await session.rpc(my_add.blob(1, 2))
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms (async)")
    try:
        ret_str: str = await session.rpc(custom_timeout_2ms.blob(), timeout_sec=0.002)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec (async)")
    try:
        ret_str: str = await session.rpc(custom_timeout_1sec.blob(), timeout_sec=1)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. execute function that calls the other function (async)")
    ret_val = await session.rpc(use_my_add.blob(1, 2))
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid (async)")
    surface_uid: dict[str, str] = await session.rpc(get_surface_uid.blob(surface_name="surface 1"))
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface (async)")
    await session.rpc(rename_surface.blob(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = await session.rpc(get_surface_uid.blob(surface_name="surface 2"))
    print(surface_uid)
    await session.rpc(rename_surface.blob(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = await session.rpc(get_surface_uid.blob(surface_name="surface 1"))
    print(surface_uid)

    # time-related functions
    print("7. get current time (mymodule) (async)")
    current_time: str = await session.rpc(my_time.blob())
    print(f"- result: {current_time}")

    print("8. get current time with note (mymodule) (async)")
    time_with_note: str = await session.rpc(my_time_with_note.blob(note="test note"))
    print(f"- result: {time_with_note}")

    # module2 functions
    print("9. sleep 50ms (module2) (async)")
    result: str = await session.rpc(sleep_50ms.blob())
    print(f"- result: {result}")

    print("10. get current time (module2) (async)")
    time_module2: str = await session.rpc(my_time_module2.blob())
    print(f"- result: {time_module2}")

    print("11. get surface uid with time (module2) (async)")
    surface_with_time: dict[str, str] = await session.rpc(get_surface_uid_with_time.blob(surface_name="surface 1"))
    print(surface_with_time)

    print("12. get typed surface (module2) (async)")
    typed_surface = await session.rpc(get_typed_surface.blob(surface_name="surface 1"))
    print(typed_surface)

async def main():
    print("")
    print("=" * 60)
    print("with context example")
    print("=" * 60)
    await without_context()

    print("")
    print("=" * 60)
    print("without context example")
    print("=" * 60)
    await without_context()
    

if __name__ == "__main__":
    asyncio.run(main())
