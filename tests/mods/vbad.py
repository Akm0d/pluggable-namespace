"""
Fail to load to test load errors making sure to find the module under
the defined __virtualname__
"""

__virtualname__ = "virtual_bad"


async def __virtual__(hub):
    return "Failed to load virtual bad"


async def func(hub):
    return "wha?"
