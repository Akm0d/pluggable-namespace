"""
module used while testing mock hubs provided in 'testing'.
"""

__contracts__ = ["testing"]


async def noparam(hub):
    pass


async def echo(hub, param):
    return param


async def signature_func(hub, param1, param2="default"):
    pass


async def attr_func(hub):
    pass


attr_func.test = True
attr_func.__test__ = True


async def async_echo(hub, param):
    return param
