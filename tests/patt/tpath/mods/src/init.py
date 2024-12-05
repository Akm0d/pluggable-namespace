async def init(hub, *args, **kwargs):
    return await hub.patt.inst.init(*args, **kwargs)


async def create(hub, *args, **kwargs):
    return await hub.patt.inst.create(*args, **kwargs)


async def get(hub, *args, **kwargs):
    return await hub.patt.inst.get(*args, **kwargs)


async def delete(hub, *args, **kwargs):
    return await hub.patt.inst.delete(*args, **kwargs)
