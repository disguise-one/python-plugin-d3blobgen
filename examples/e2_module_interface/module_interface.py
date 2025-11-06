from d3blobgen.session import D3Session
from e2_module_interface.module_interface_blob import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    use_my_add,
    get_surface_uid,
    rename_surface,
)

DESIGNER_IP = "localhost"
DESIGNER_PORT = 80

def with_context():
    with D3Session(DESIGNER_IP, DESIGNER_PORT, ["mymodule"]) as session:
        # mymodule will be register by context __enter__
        print("1. execute over plugin")
        ret_val: int = session.rpc(my_add.blob(1, 2))
        print(f"- result: {ret_val}")

        print("2. custom timeout 2ms")
        try:
            ret_str: str = session.rpc(custom_timeout_2ms.blob(), timeout_sec=0.002)
            print(f"- result: {ret_str}")
        except Exception as e:
            print(e)

        print("3. custom timeout 1sec")
        try:
            ret_str: str = session.rpc(custom_timeout_1sec.blob(), timeout_sec=1)
            print(f"- result: {ret_str}")
        except Exception as e:
            print(e)

        print("4. execute function that calls the other function")
        ret_val = session.rpc(use_my_add.blob(1, 2))
        print(f"- result: {ret_val}")

        # access resource in Designer
        print("5. get surface uid")
        surface_uid: dict[str, str] = session.rpc(get_surface_uid.blob(surface_name="surface 1"))
        print(surface_uid)

        # update resource in Designer
        print("6. rename surface")
        session.rpc(rename_surface.blob(surface_name="surface 1", new_surface_name="surface 2"))
        surface_uid = session.rpc(get_surface_uid.blob(surface_name="surface 2"))
        print(surface_uid)
        session.rpc(rename_surface.blob(surface_name="surface 2", new_surface_name="surface 1"))
        surface_uid = session.rpc(get_surface_uid.blob(surface_name="surface 1"))
        print(surface_uid)


def without_context():
    # init session to communicate with d3
    session = D3Session(DESIGNER_IP, DESIGNER_PORT)

    # register all d3function modules
    respond: dict[str, bool] = session.register_all_modules()
    print(f"register module result: {respond}")

    print("1. execute over plugin")
    ret_val: int = session.rpc(my_add.blob(1, 2))
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms")
    try:
        ret_str: str = session.rpc(custom_timeout_2ms.blob(), timeout_sec=0.002)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec")
    try:
        ret_str: str = session.rpc(custom_timeout_1sec.blob(), timeout_sec=1)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. execute function that calls the other function")
    ret_val = session.rpc(use_my_add.blob(1, 2))
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid")
    surface_uid: dict[str, str] = session.rpc(get_surface_uid.blob(surface_name="surface 1"))
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface")
    session.rpc(rename_surface.blob(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = session.rpc(get_surface_uid.blob(surface_name="surface 2"))
    print(surface_uid)
    session.rpc(rename_surface.blob(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = session.rpc(get_surface_uid.blob(surface_name="surface 1"))
    print(surface_uid)

def main():
    print("")
    print("=" * 60)
    print("with context example")
    print("=" * 60)
    with_context()

    print("")
    print("=" * 60)
    print("without context example")
    print("=" * 60)
    without_context()


if __name__ == "__main__":
    main()
