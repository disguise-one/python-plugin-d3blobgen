from d3blobgen.core import register_all_d3functions
from d3blobgen.utils import d3_api_plugin
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
    DESIGNER_IP = "localhost"
    DESIGNER_PORT = 80

    # must register all modules first
    register_all_d3functions(DESIGNER_IP, DESIGNER_PORT)

    # execute function that uses datetime package
    print("1. execute function that uses datetime package")
    ret_val: str = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, my_time.blob()).returnValue
    print(f"- result: {ret_val}")

    # execute function that calls another function in same module
    print("2. execute function that calls another function in same module")
    ret_val = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, my_time_with_note.blob("test note")).returnValue
    print(f"- result: {ret_val}")

    # execute function from module2
    print("3. execute function from module2")
    ret_val = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, my_time_module2.blob()).returnValue
    print(f"- result: {ret_val}")

    # execute function that uses time.sleep
    print("4. execute function that uses time.sleep")
    ret_val = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, sleep_50ms.blob()).returnValue
    print(f"- result: {ret_val}")

    # test exception when calling function from different module
    print("5. exception when calling function from different module")
    try:
        d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, will_raise_if_call_different_module_function.json())
    except Exception as e:
        print(f"- error: {e}")

    # access resource with custom data (time)
    print("6. get surface uid with time")
    surface_data: dict[str, str] = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_surface_uid_with_time.blob(surface_name="surface 1")).returnValue
    print(surface_data)

    # access resource with TypedDict return type
    print("7. get typed surface")
    typed_surface: Surface = d3_api_plugin(DESIGNER_IP, DESIGNER_PORT, get_typed_surface.blob(surface_name="surface 1")).returnValue
    print(typed_surface)
    print(typed_surface["name"])
    

if __name__ == "__main__":
    main()
