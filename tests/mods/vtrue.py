__virtualname__ = "truev"


async def __virtual__(hub):
    return True


async def present(hub):
    return True
