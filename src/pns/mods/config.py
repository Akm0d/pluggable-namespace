async def load(hub, *args, **kwargs):
    return await hub.config.init.load(*args, **kwargs)
