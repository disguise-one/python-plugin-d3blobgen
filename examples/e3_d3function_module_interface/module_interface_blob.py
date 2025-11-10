from d3blobgen.core import d3function, add_packages_in_current_file
from typing import TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import *

import datetime
import time

"""
!!! Note: 
It's very important to put `add_packages_in_current_file` with
the module name to use it on Designer side.

For example, `my_time` will only work if
- `import datetime` exists in this file
- `add_packages_in_current_file` exists with proper module name  
"""
add_packages_in_current_file("mymodule")
add_packages_in_current_file("module2")

# Simple d3function examples
@d3function("mymodule")
def my_add(a: int, b: int) -> int:
    return a + b

@d3function("mymodule")
def custom_timeout_2ms() -> str:
    import time
    time.sleep(0.1)
    return "success"

@d3function("mymodule")
def custom_timeout_1sec() -> str:
    import time
    time.sleep(0.1)
    return "success"

@d3function("mymodule")
def use_my_add(a: int, b: int) -> int:
    return my_add(a, b)

@d3function("mymodule")
def get_surface_uid(surface_name: str) -> dict[str, str]:
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    return {
        "name": surface.path.filename,
        "uid": str(surface.uid)
    }


# d3function with builtin packages examples
@d3function("mymodule")
def rename_surface(surface_name: str, new_surface_name: str):
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    surface.rename(surface.path.replaceFilename(new_surface_name))

@d3function("mymodule")
def my_time() -> str:
    return str(datetime.datetime.now())

@d3function("mymodule")
def my_time_with_note(note: str) -> str:
    return "{}, Note: {}".format(my_time(), note)

@d3function("module2") # module name is `module2` not `mymodule`
def will_raise_if_call_different_module_function() -> str:
    return my_time()

@d3function("module2")
def sleep_50ms() -> str:
    time.sleep(0.05)
    return "after 50ms"

@d3function("module2")
def my_time_module2() -> str:
    return str(datetime.datetime.now())

@d3function("module2")
def get_surface_uid_with_time(surface_name: str) -> dict[str, str]:
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    return {
        "name": surface.path.filename,
        "uid": str(surface.uid),
        "time": my_time_module2()
    }

# TypedDict is supported, but not pydantic BaseModel
class Surface(TypedDict):
    name: str
    uid: int
    time: str

@d3function("module2")
def get_typed_surface(surface_name: str) -> Surface:
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    return {
        "name": surface.path.filename,
        "uid": surface.uid,
        "time": my_time_module2()
    }

