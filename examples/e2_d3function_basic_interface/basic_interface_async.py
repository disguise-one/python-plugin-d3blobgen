import asyncio
from d3blobgen.session import D3AsyncSession
from e2_d3function_basic_interface.basic_interface_blobs import (
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

    # init session to communicate with d3
    session = D3AsyncSession(DESIGNER_IP, DESIGNER_PORT)

    # register all d3function modules
    await session.register_all_modules()

    print("1. execute over plugin (async)")
    ret_val_from_plugin: int = await session.rpc(my_add.payload(1, 2))
    print(f"- result: {ret_val_from_plugin}")

    print("2. custom timeout 2ms (async)")
    try:
        ret_str: str = await session.rpc(custom_timeout_2ms.payload(), timeout_sec=0.002)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec (async)")
    try:
        ret_str = await session.rpc(custom_timeout_1sec.payload(),  timeout_sec=1)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("4. exception over execute (async)")
    try:
        await session.rpc(my_exception.payload())
    except Exception as e:
        print(e)

    # access resource in Designer
    print("5. get surface uid (async)")
    surface_uid: dict[str, str] = await session.rpc(get_surface_uid.payload(surface_name="surface 1"))
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface (async)")
    await session.rpc(rename_surface.payload(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = await session.rpc(get_surface_uid.payload(surface_name="surface 2"))
    print(surface_uid)
    await session.rpc(rename_surface.payload(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = await session.rpc(get_surface_uid.payload(surface_name="surface 1"))
    print(surface_uid)


if __name__ == "__main__":
    asyncio.run(main())
