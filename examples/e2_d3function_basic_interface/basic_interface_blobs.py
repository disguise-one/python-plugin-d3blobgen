from d3blobgen.core import d3function
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import *


@d3function()
def my_add(a: int, b: int) -> int:
    return a + b

@d3function()
def my_print():
    print("Hello world")

@d3function()
def my_exception():
    raise RuntimeError("My Runtime Error")

@d3function()
def custom_timeout_2ms():
    return "Hello world in 2ms"

@d3function()
def custom_timeout_1sec():
    return "Hello world in 1sec"

@d3function()
def get_surface_uid(surface_name: str) -> dict[str, str]:
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    return {
        "name": surface.path.filename,
        "uid": str(surface.uid)
    }

@d3function()
def rename_surface(surface_name: str, new_surface_name: str):
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    surface.rename(surface.path.replaceFilename(new_surface_name))

