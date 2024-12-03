"""
Fail to load to test load errors
"""

__virtualname__ = "bad"


async def __virtual__(hub):
    return "Failed to load bad"


async def func(hub):
    return "wha?"
