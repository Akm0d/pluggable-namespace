__virtualname__ = "yaml"


async def display(hub, data):
    """
    Print the raw data
    """

    # # yaml safe_dump doesn't know how to represent subclasses of dict.
    # # this registration allows arbitrary dict types to be represented
    # # without conversion to a regular dict.
    def any_dict_representer(dumper, data):
        return dumper.represent_dict(data)

    hub.lib.yaml.add_multi_representer(
        dict, any_dict_representer, Dumper=hub.lib.yaml.SafeDumper
    )
    hub.lib.yaml.add_multi_representer(
        hub.lib.collections.abc.Mapping,
        any_dict_representer,
        Dumper=hub.lib.yaml.SafeDumper,
    )

    return hub.lib.yaml.safe_dump(data)
