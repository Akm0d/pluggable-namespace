__virtualname__ = "vname"


async def __virtual__(hub):
    return True


async def func(hub):
    return "wha? Yep!"
