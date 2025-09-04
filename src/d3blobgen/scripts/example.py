from d3blobgen import d3function

# Function without module
@d3function()
def get_camera_uid_no_module(camera_name:str) -> dict[str, str]:
    import d3
    camera: d3.MixedRealitySet = d3.resourceManager.load(
        'objects/camera/{}.apx'.format(camera_name),
        d3.Camera)
    return { "uid": camera.uid }

# Function with module my_d3_module
@d3function(module_name="my_d3_module")
def get_mrset_uid(mrset_name:str) -> dict[str, str]:
    import d3
    mr_set: d3.MixedRealitySet = d3.resourceManager.load(
        'objects/mixedrealityset/{}.apx'.format(mrset_name),
        d3.MixedRealitySet)
    return { "uid": mr_set.uid }

# Function with module my_d3_module
@d3function(module_name="my_d3_module")
def get_camera_uid(camera_name:str) -> dict[str, str]:
    import d3
    camera: d3.MixedRealitySet = d3.resourceManager.load(
        'objects/camera/{}.apx'.format(camera_name),
        d3.Camera)
    return { "uid": camera.uid }
