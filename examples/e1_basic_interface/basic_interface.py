from examples.e1_basic_interface.basic_interface_blobs import (
    my_add,
    custom_timeout_2ms,
    custom_timeout_1sec,
    my_exception,
    get_surface_uid,
    rename_surface,
)


def main():
    # normal function call
    ret_val: int = my_add(1, 2)
    print("1. normal function call")
    print(f"- result: {ret_val}")

    # execute over Designer plugin
    print("2. execute over plugin")
    ret_val_from_plugin = my_add.execute(1, 2)
    print(f"- result: {ret_val_from_plugin}")

    print("3. custom timeout 2ms")
    try:
        ret_str: str = custom_timeout_2ms.execute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    print("4. custom timeout 1sec")
    try:
        ret_str: str = custom_timeout_1sec.execute()
        print(f"- result: {ret_str}")
    except Exception as e:
        print(e)

    # test exception
    print("5. exception over execute")
    try:
        my_exception.execute()
    except Exception as e:
        print(e)

    # access resource in Designer
    print("6. get surface uid")
    surface_uid: dict[str, str] = get_surface_uid.execute(surface_name="surface 1")
    print(surface_uid)

    # update resource in Designer
    print("7. rename surface")
    rename_surface.execute(surface_name="surface 1", new_surface_name="surface 2")
    surface_uid = get_surface_uid.execute(surface_name="surface 2")
    print(surface_uid)
    rename_surface.execute(surface_name="surface 2", new_surface_name="surface 1")
    surface_uid = get_surface_uid.execute(surface_name="surface 1")
    print(surface_uid)

if __name__ == "__main__":
    main()

