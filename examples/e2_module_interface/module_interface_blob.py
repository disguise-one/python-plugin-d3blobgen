from d3blobgen.core import d3function
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import *


@d3function("mymodule")
def my_add(a: int, b: int) -> int:
    return a + b

@d3function("mymodule", timeout_sec=0.002)
def custom_timeout_2ms() -> str:
    import time
    time.sleep(0.1)
    return "success"

@d3function("mymodule", timeout_sec=1)
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

@d3function("mymodule")
def rename_surface(surface_name: str, new_surface_name: str):
    surface: Screen2 = resourceManager.load(
        Path('objects/screen2/{}.apx'.format(surface_name)),
        Screen2
    )
    surface.rename(surface.path.replaceFilename(new_surface_name))
