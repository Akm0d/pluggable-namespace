import os


async def __init__(hub):
    hub.FORK_NEST_INIT = True


async def var(hub):
    return hub.FORK_NEST_INIT


async def pid(hub):
    return os.getpid()
