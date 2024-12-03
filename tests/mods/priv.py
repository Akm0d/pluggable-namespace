async def public(hub):
    return await _private(hub)


async def _private(hub):
    return hub.opts  # pylint: disable=undefined-variable
