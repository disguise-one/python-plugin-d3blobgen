from d3blobgen import d3function

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import d3

# Function without module
@d3function()
def get_camera_uid_no_module(camera_name:str) -> dict[str, str]:
    camera = d3.resourceManager.load(
        d3.Path('objects/camera/{}.apx'.format(camera_name)),
        d3.Camera)
    return { "uid": str(camera.uid) }

# Function with module my_d3_module
@d3function(module_name="my_d3_module")
def get_mrset_uid(mrset_name:str) -> dict[str, str]:
    mr_set = d3.resourceManager.load(
        d3.Path('objects/mixedrealityset/{}.apx'.format(mrset_name)),
        d3.MixedRealitySet)
    return { "uid": str(mr_set.uid) }

# Function with module my_d3_module
@d3function(module_name="my_d3_module")
def get_camera_uid(camera_name:str) -> dict[str, str]:
    camera: d3.MixedRealitySet = d3.resourceManager.load(
        d3.Path('objects/camera/{}.apx'.format(camera_name)),
        d3.Camera)
    return { "uid": str(camera.uid) }
