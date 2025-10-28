from d3blobgen.core import d3function, add_packages_in_current_file
from typing import TYPE_CHECKING, TypedDict
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import *

import datetime
import time

# all packages in this file will be registered to module
# so all d3function can access them as well
add_packages_in_current_file("mymodule")
add_packages_in_current_file("module2")

@d3function("mymodule")
def my_time() -> str:
    return str(datetime.datetime.now())

@d3function("mymodule")
def my_time_with_note(note: str) -> str:
    return "{}, Note: {}".format(my_time(), note)

@d3function("module2")
def will_raise_if_call_different_module_function() -> str:
    return my_time()

@d3function("module2")
def sleep_50ms() -> str:
    time.sleep(0.05)
    return "after 50ms"

def same_module_function_access(note: str) -> str:
    return "{}, Note: {}".format(sleep_50ms(), note)

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
