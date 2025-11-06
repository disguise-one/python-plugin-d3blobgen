from d3blobgen.utils import d3_api_plugin
from examples.e1_basic_interface.basic_interface_blobs import (
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

    # normal function call
    ret_val: int = my_add(1, 2)
    print("1. normal function call")
    print(f"- result: {ret_val}")

    # execute over Designer plugin
    print("2. execute over plugin")
    ret_val_from_plugin = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, my_add.blob(1, 2)).returnValue
    print(f"- result: {ret_val_from_plugin}")

    print("3. custom timeout 2ms")
    try:
        ret_str: str = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_2ms.blob(), timeout_sec=0.002).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. custom timeout 1sec")
    try:
        ret_str: str = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_1sec.blob(), timeout_sec=1).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("5. exception over execute")
    try:
        d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, my_exception.json())
    except Exception as e:
        print(e)

    # access resource in Designer
    print("6. get surface uid")
    surface_uid: dict[str, str] = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 1")).returnValue
    print(surface_uid)

    # update resource in Designer
    print("7. rename surface")
    d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.json(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 2")).returnValue
    print(surface_uid)
    d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.json(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.blob(surface_name="surface 1")).returnValue
    print(surface_uid)

if __name__ == "__main__":
    main()

