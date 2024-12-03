async def __virtual__(hub):
    return hub.OPT.v1.load, "hub.OPT.v1.load was set to False"


A = 1


async def a(hub):
    return A
