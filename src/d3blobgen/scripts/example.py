from d3blobgen import d3function

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from d3blobgen.scripts.d3 import * # type: ignore[reportMissingModuleSource]

# Function without module
@d3function()
def get_camera_uid_no_module(camera_name:str) -> dict[str, str]:
    camera: Camera = resourceManager.load(
        Path('objects/camera/{}.apx'.format(camera_name)),
        Camera)
    return { "uid": str(camera.uid) }

# Function with module my_d3_module
@d3function(module_name="my_d3_module")
def get_mrset_uid(mrset_name:str) -> dict[str, str]:
    mr_set: MixedRealitySet = resourceManager.load(
        Path('objects/mixedrealityset/{}.apx'.format(mrset_name)),
        MixedRealitySet)
    return { "uid": str(mr_set.uid) }

# Function with module my_d3_module
@d3function(module_name="my_d3_module")
def get_camera_uid(camera_name:str) -> dict[str, str]:
    camera: Camera = resourceManager.load(
        Path('objects/camera/{}.apx'.format(camera_name)),
        Camera)
    return { "uid": str(camera.uid) }

@d3function(module_name="my_d3_module")
def rename_camera(cam_name:str, new_cam_name:str) -> None:
    camera: Camera = resourceManager.load(
        Path('objects/camera/{}.apx'.format(cam_name)),
        Camera)
    camera.rename(camera.path.replaceFilename(new_cam_name))

@d3function(module_name="my_d3_module")
def return_increment(input: int) -> int:
    return input + 1

@d3function(module_name="my_d3_module")
def get_projection_surface(surface_name: str) -> dict[str, str]:
    surface: MixedRealitySet = resourceManager.load(
    Path('objects/screen2/{}.apx'.format(surface_name)),
    Screen2)
    
    return {
        "name": surface.path.filename,
        "uid": str(surface.uid),
    }

@d3function(module_name="my_d3_module")
def rename_projection_surface(surface_name:str, new_surface_name:str) -> None:
    surface: MixedRealitySet = resourceManager.load(
    Path('objects/screen2/{}.apx'.format(surface_name)),
    Screen2)
    
    surface.rename(surface.path.replaceFilename(new_surface_name))
