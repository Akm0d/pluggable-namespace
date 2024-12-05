async def bar(hub):
    return await hub.mods.test.ping()  # pylint: disable=undefined-variable
