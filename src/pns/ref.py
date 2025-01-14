def last(hub, ref) -> object:
    """
    Takes a string that references the desired ref and returns the last object
    called out in that ref
    """
    refs = path(hub, ref)
    return refs.pop()


def path(hub, ref) -> list[object]:
    """
    Returns a list of references up to the named ref
    """
    ret = [hub]

    if isinstance(ref, str):
        ref = ref.split(".")

    root = hub
    for chunk in ref:
        root = getattr(root, chunk)
        ret.append(root)
    return ret


def find(hub, ref: str) -> object:
    """
    Take a string that represents an attribute nested underneath the hub.
    Parse the string and retrieve the object form the hub.

    Args:
        hub (pns.hub.Hub): The global namespace.
        ref (str): A string separated by "." with each part being a level deeper into objects on the hub.

    Returns:
        any: The object found on the hub
    """
    # Get the named reference from the hub
    finder = hub
    parts = ref.split(".")
    for p in parts:
        if not p:
            continue
        try:
            # Grab the next attribute in the reference
            finder = getattr(finder, p)
            continue
        except AttributeError:
            try:
                # It might be a dict-like object, try getitem
                finder = finder.__getitem__(p)
                continue
            except TypeError:
                # It might be an iterable, if the next part of the ref is a digit try to access the index
                if p.isdigit() and isinstance(finder, hub.lib.typing.Iterable):
                    finder = tuple(finder).__getitem__(int(p))
                    continue
            raise
    return finder
