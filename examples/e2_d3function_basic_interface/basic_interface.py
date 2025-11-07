from d3blobgen.session import D3Session
from e1_basic_interface.basic_interface_blobs import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    my_exception,
    get_surface_uid,
    rename_surface,
)


def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # init session to communicate with d3
    session = D3Session(DESIGNER_IP, DESIGNER_PORT)

    # register all d3function modules
    session.register_all_modules()
    
    print("1. normal function call")
    ret_val: int = my_add(1, 2)
    print(f"- result: {ret_val}")

    print("2. execute over plugin")
    ret_val_from_plugin: int = session.rpc(my_add.blob(1, 2))
    print(f"- result: {ret_val_from_plugin}")

    print("3. custom timeout 2ms")
    try:
        ret_str: str = session.rpc(custom_timeout_2ms.blob(), timeout_sec=0.002)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. custom timeout 1sec")
    try:
        ret_str: str = session.rpc(custom_timeout_1sec.blob(), timeout_sec=1)
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("5. exception over execute")
    try:
        session.rpc(my_exception.blob())
    except Exception as e:
        print(e)

    # access resource in Designer
    print("6. get surface uid")
    surface_uid: dict[str, str] = session.rpc(get_surface_uid.blob(surface_name="surface 1"))
    print(surface_uid)

    # update resource in Designer
    print("7. rename surface")
    session.rpc(rename_surface.blob(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = session.rpc(get_surface_uid.blob(surface_name="surface 2"))
    print(surface_uid)
    session.rpc(rename_surface.blob(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = session.rpc(get_surface_uid.blob(surface_name="surface 1"))
    print(surface_uid)

if __name__ == "__main__":
    main()

