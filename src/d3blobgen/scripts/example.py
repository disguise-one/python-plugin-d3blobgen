def mrset_fn_with_args(mr_set_name: str) -> list:
    # Get list of displays objects from MR set
    import d3
    mr_set: d3.MixedRealitySet = d3.resourceManager.load(
        f'objects/mixedrealityset/{mr_set_name}.apx',
        d3.MixedRealitySet)

    if mr_set is None:
        print("MR set not found")
        return []

    display_objects = []
    for obj in mr_set.onStageObjects:
        print("Onstage obj path: " + str(obj.description))
        if isinstance(obj, d3.Display):
            display_objects.append({
                "uid": str(obj.uid),
                "name": str(obj.description)
            })

    return display_objects

def mrset_fn_without_args() -> list:
    # Get list of displays objects from MR set
    import d3
    mr_set: d3.MixedRealitySet = d3.resourceManager.load(
        f'objects/mixedrealityset/example_mrsets.apx',
        d3.MixedRealitySet)

    if mr_set is None:
        print("MR set not found")
        return []

    display_objects = []
    for obj in mr_set.onStageObjects:
        print("Onstage obj path: " + str(obj.description))
        if isinstance(obj, d3.Display):
            display_objects.append({
                "uid": str(obj.uid),
                "name": str(obj.description)
            })

    return display_objects
