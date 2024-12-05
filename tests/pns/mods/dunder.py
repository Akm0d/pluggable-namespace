async def __virtual__(hub):
    return True


async def __init__(hub):
    hub._.FOO = "bar"
    assert hub._.__name__.endswith(".dunder"), f"name is {hub._.__name__}, not dunder"


async def func(hub):
    # Make sure that things defined in the init show up properly
    assert hub._.FOO == "bar"
    assert hub._.FOO == hub.mods.dunder.FOO
