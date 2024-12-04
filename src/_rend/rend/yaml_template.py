"""
Render yte data
"""

__virtualname__ = "yte"


async def __virtual__(hub):
    if "aio_yte" not in hub.lib._imports:
        return False, "Missing yte library"
    return True


async def render(hub, data):
    """
    Render the given data through yte
    """
    if isinstance(data, bytes):
        data = data.decode("utf-8")

    variables = {"hub": hub}

    ret = await hub.lib.aio_yte.aprocess_yaml(data, variables=variables)

    return ret
