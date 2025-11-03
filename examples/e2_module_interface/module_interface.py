from d3blobgen.core import register_all_d3functions, register_module_d3functions
from d3blobgen.utils import d3_api_plugin
from examples.e2_module_interface.module_interface_blob import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    use_my_add,
    get_surface_uid,
    rename_surface,
)

def main():
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # must register module first
    register_all_d3functions(DESIGNER_IP)

    # you can register specific module as well
    # register_module_d3functions(DESIGNER_IP, "mymodule")

    # execute over Designer plugin
    print("1. execute over plugin")
    ret_val = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, my_add.get_typed_execute_blob(1, 2)).returnValue
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms")
    try:
        ret_str: str = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_2ms.get_typed_execute_blob(), timeout_ms=2).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec")
    try:
        ret_str: str = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, custom_timeout_1sec.get_typed_execute_blob(), timeout_ms=1000).returnValue
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("4. execute function that calls the other function")
    ret_val = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, use_my_add.get_typed_execute_blob(1, 2)).returnValue
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid")
    surface_uid: dict[str, str] = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.get_typed_execute_blob(surface_name="surface 1")).returnValue
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface")
    d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.get_execute_blob(surface_name="surface 1", new_surface_name="surface 2"))
    surface_uid = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.get_typed_execute_blob(surface_name="surface 2")).returnValue
    print(surface_uid)
    d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, rename_surface.get_execute_blob(surface_name="surface 2", new_surface_name="surface 1"))
    surface_uid = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid.get_typed_execute_blob(surface_name="surface 1")).returnValue
    print(surface_uid)

if __name__ == "__main__":
    main()

