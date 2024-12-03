# pylint: disable=undefined-variable


async def __init__(hub):
    hub.context["subinit"] = True


async def inited(hub):
    return "subinit" in hub.context
