from d3blobgen import *
from d3blobgen.scripts.example import *


@d3function()
def normal_function_no_module(a: int, b: str):
    return "{}, {}".format(a, b)

@d3function(module_name="my_normal_fn_module")
def normal_function1(a: int, b: str):
    return "{}, {}".format(a, b)

@d3function("my_normal_fn_module")
def normal_function2(a: int, b: str):
    return "{}, {}".format(a, b)


def main():
    print("\n1. get_all_d3functions")
    for module_name, func_name in get_all_d3functions():
        print(f"{module_name}, {func_name}")

    print("\n2. get_all_modules")
    print(get_all_modules())

    print("\n3. get_module_register_blob")
    print(D3Function.get_module_register_blob("my_d3_module"))

    print("\n3. get_execute_blob")
    print(get_camera_uid_no_module.get_execute_blob("my_camera1"))
    print(get_mrset_uid.get_execute_blob("my_mrset"))
    print(get_camera_uid.get_execute_blob("my_cam"))
    
    print(normal_function_no_module.get_execute_blob(3, "d"))
    print(normal_function1.get_execute_blob(1, "b"))
    print(normal_function2.get_execute_blob(2, "c"))


if __name__ == "__main__":
    main()
