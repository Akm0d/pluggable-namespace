"""
used to test the sub init system
"""

# pylint: disable=undefined-variable


async def __init__(hub):
    """
    Add a value to the context
    """
    hub.context = {}
    hub.context["init"] = True
    await hub._.inited()


async def inited(hub):
    return "init" in hub.context
