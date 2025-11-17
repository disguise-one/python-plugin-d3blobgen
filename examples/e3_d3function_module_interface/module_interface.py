from d3blobgen.session import D3Session
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

def with_context():
    with D3Session(DESIGNER_IP, DESIGNER_PORT, ["mymodule", "module2"]) as session:
        # mymodule will be register by context __enter__
        print("1. execute over plugin")
        ret_val: int = session.rpc(my_add.payload(1, 2))
        print(f"- result: {ret_val}")

        print("2. custom timeout 2ms")
        try:
            ret_str: str = session.rpc(custom_timeout_2ms.payload(), timeout_sec=0.002)
            print(f"- result: {ret_str}")
        except Exception as e:
            print(e)

        print("3. custom timeout 1sec")
        try:
            ret_str: str = session.rpc(custom_timeout_1sec.payload(), timeout_sec=1)
            print(f"- result: {ret_str}")
        except Exception as e:
            print(e)

        print("4. execute function that calls the other function")
        ret_val = session.rpc(use_my_add.payload(1, 2))
        print(f"- result: {ret_val}")

        # access resource in Designer
        print("5. get surface uid")
        surface_uid: dict[str, str] = session.rpc(get_surface_uid.payload(surface_name="surface 1"))
        print(surface_uid)

        # update resource in Designer
        print("6. rename surface")
        session.rpc(rename_surface.payload(surface_name="surface 1", new_surface_name="surface 2"))
        surface_uid = session.rpc(get_surface_uid.payload(surface_name="surface 2"))
        print(surface_uid)
        session.rpc(rename_surface.payload(surface_name="surface 2", new_surface_name="surface 1"))
        surface_uid = session.rpc(get_surface_uid.payload(surface_name="surface 1"))
        print(surface_uid)

        # time-related functions
        print("7. get current time (mymodule)")
        current_time: str = session.rpc(my_time.payload())
        print(f"- result: {current_time}")

        print("8. get current time with note (mymodule)")
        time_with_note: str = session.rpc(my_time_with_note.payload(note="test note"))
        print(f"- result: {time_with_note}")

        # module2 functions
        print("9. sleep 50ms (module2)")
        result: str = session.rpc(sleep_50ms.payload())
        print(f"- result: {result}")

        print("10. get current time (module2)")
        time_module2: str = session.rpc(my_time_module2.payload())
        print(f"- result: {time_module2}")

        print("11. get surface uid with time (module2)")
        surface_with_time: dict[str, str] = session.rpc(get_surface_uid_with_time.payload(surface_name="surface 1"))
        print(surface_with_time)

        print("12. get typed surface (module2)")
        typed_surface = session.rpc(get_typed_surface.payload(surface_name="surface 1"))
        print(typed_surface)


def without_context():
    # init session to communicate with d3
    session = D3Session(DESIGNER_IP, DESIGNER_PORT)

    # register all d3function modules
    respond: dict[str, bool] = session.register_all_modules()
    print(f"register module result: {respond}")

    print("1. execute over plugin")
    ret_val: int = session.rpc(my_add.payload(1, 2))
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms")
    try:
        ret_str: str = session.rpc(custom_timeout_2ms.payload(), timeout_sec=0.002)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec")
    try:
        ret_str: str = session.rpc(custom_timeout_1sec.payload(), timeout_sec=1)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. execute function that calls the other function")
    ret_val = session.rpc(use_my_add.payload(1, 2))
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid")
    surface_uid: dict[str, str] = session.rpc(get_surface_uid.payload(surface_name="surface 1"))
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface")
    session.rpc(rename_surface.payload(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = session.rpc(get_surface_uid.payload(surface_name="surface 2"))
    print(surface_uid)
    session.rpc(rename_surface.payload(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = session.rpc(get_surface_uid.payload(surface_name="surface 1"))
    print(surface_uid)

    # time-related functions
    print("7. get current time (mymodule)")
    current_time: str = session.rpc(my_time.payload())
    print(f"- result: {current_time}")

    print("8. get current time with note (mymodule)")
    time_with_note: str = session.rpc(my_time_with_note.payload(note="test note"))
    print(f"- result: {time_with_note}")

    # module2 functions
    print("9. sleep 50ms (module2)")
    result: str = session.rpc(sleep_50ms.payload())
    print(f"- result: {result}")

    print("10. get current time (module2)")
    time_module2: str = session.rpc(my_time_module2.payload())
    print(f"- result: {time_module2}")

    print("11. get surface uid with time (module2)")
    surface_with_time: dict[str, str] = session.rpc(get_surface_uid_with_time.payload(surface_name="surface 1"))
    print(surface_with_time)

    print("12. get typed surface (module2)")
    typed_surface = session.rpc(get_typed_surface.payload(surface_name="surface 1"))
    print(typed_surface)

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
