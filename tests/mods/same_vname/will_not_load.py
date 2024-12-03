__virtualname__ = "vname"


async def __virtual__(hub):
    return False, "Do not load!"


async def func(hub):
    return "wha? No! No! No!!!!!"
