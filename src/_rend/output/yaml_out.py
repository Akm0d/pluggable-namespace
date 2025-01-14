__virtualname__ = "yaml"


def _any_dict_representer(dumper, data):
    """
    yaml safe_dump doesn't know how to represent subclasses of dict.
    This registration allows arbitrary dict types to be represented
    without conversion to a regular dict.
    """
    return dumper.represent_dict(data)


def _unknown_object_representer(dumper, obj):
    """
    Define a custom representer for unknown (or generic) objects
    """
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(obj))


async def display(hub, data):
    """
    Print the raw data
    """
    hub.lib.yaml.add_multi_representer(
        dict, _any_dict_representer, Dumper=hub.lib.yaml.SafeDumper
    )
    hub.lib.yaml.add_multi_representer(
        hub.lib.collections.abc.Mapping,
        _any_dict_representer,
        Dumper=hub.lib.yaml.SafeDumper,
    )

    hub.lib.yaml.add_multi_representer(
        object, _unknown_object_representer, Dumper=hub.lib.yaml.SafeDumper
    )

    return hub.lib.yaml.safe_dump(data)
