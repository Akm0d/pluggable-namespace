async def ping(hub):
    return True


async def echo(hub, *args, **kwargs):
    return args, kwargs
