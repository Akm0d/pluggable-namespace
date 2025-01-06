async def pre_func1(hub, ctx):
    return False


async def pre_func2(hub, ctx):
    return False, "custom message"


async def pre_afunc1(hub, ctx):
    return False


async def pre_afunc2(hub, ctx):
    return False, "custom message"


async def pre_gen1(hub, ctx):
    return False


async def pre_gen2(hub, ctx):
    return False, "custom message"


async def pre_agen1(hub, ctx):
    return False


async def pre_agen2(hub, ctx):
    return False, "custom message"
