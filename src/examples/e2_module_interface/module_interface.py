from d3blobgen.core import register_all_d3functions, register_module_d3functions
from examples.e2_module_interface.module_interface_blob import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    use_my_add,
    get_surface_uid,
    rename_surface,
)

def main():
    # must register module first
    register_all_d3functions("localhost")

    # you can register specific module as well
    # register_module_d3functions("localhost", "mymodule")

    # execute over Designer plugin
    print("1. execute over plugin")
    ret_val = my_add.execute(1, 2)
    print(f"- result: {ret_val}")

    print("2. custom timeout 2ms")
    try:
        ret_str: str = custom_timeout_2ms.execute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("3. custom timeout 1sec")
    try:
        ret_str: str = custom_timeout_1sec.execute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("4. execute function that calls the other function")
    ret_val = use_my_add.execute(1, 2)
    print(f"- result: {ret_val}")

    # access resource in Designer
    print("5. get surface uid")
    surface_uid: dict[str, str] = get_surface_uid.execute(surface_name="surface 1")
    print(surface_uid)

    # update resource in Designer
    print("6. rename surface")
    rename_surface.execute(surface_name="surface 1", new_surface_name="surface 2")
    surface_uid = get_surface_uid.execute(surface_name="surface 2")
    print(surface_uid)
    rename_surface.execute(surface_name="surface 2", new_surface_name="surface 1")
    surface_uid = get_surface_uid.execute(surface_name="surface 1")
    print(surface_uid)

if __name__ == "__main__":
    main()

