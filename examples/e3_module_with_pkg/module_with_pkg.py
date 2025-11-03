from d3blobgen.core import register_all_d3functions, register_module_d3functions
from examples.e3_module_with_pkg.module_with_pkg_blob import (
    Surface,
    my_time,
    my_time_with_note,
    will_raise_if_call_different_module_function,
    sleep_50ms,
    my_time_module2,
    get_surface_uid_with_time,
    get_typed_surface,
)

def main():
    # must register all modules first
    register_module_d3functions("localhost", "mymodule")
    register_module_d3functions("localhost", "module2")

    # you can register all module at once
    # register_all_d3functions("localhost")

    # execute function that uses datetime package
    print("1. execute function that uses datetime package")
    ret_val: str = my_time.execute()
    print(f"- result: {ret_val}")

    # execute function that calls another function in same module
    print("2. execute function that calls another function in same module")
    ret_val = my_time_with_note.execute("test note")
    print(f"- result: {ret_val}")

    # execute function from module2
    print("3. execute function from module2")
    ret_val = my_time_module2.execute()
    print(f"- result: {ret_val}")

    # execute function that uses time.sleep
    print("4. execute function that uses time.sleep")
    ret_val = sleep_50ms.execute()
    print(f"- result: {ret_val}")

    # test exception when calling function from different module
    print("5. exception when calling function from different module")
    try:
        will_raise_if_call_different_module_function.execute()
    except Exception as e:
        print(f"- error: {e}")

    # access resource with custom data (time)
    print("6. get surface uid with time")
    surface_data: dict[str, str] = get_surface_uid_with_time.execute(surface_name="surface 1")
    print(surface_data)

    # access resource with TypedDict return type
    print("7. get typed surface")
    typed_surface: Surface = get_typed_surface.execute(surface_name="surface 1")
    print(typed_surface)
    print(typed_surface["name"])
    

if __name__ == "__main__":
    main()
