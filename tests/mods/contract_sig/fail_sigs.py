async def __virtual__(hub):
    return getattr(hub, "LOAD_FAIL", False), "Plugin not enabled"


async def args(hub, **__): ...


async def kwargs(hub, *_): ...


async def args_kwargs(hub): ...


async def async_func(hub): ...
