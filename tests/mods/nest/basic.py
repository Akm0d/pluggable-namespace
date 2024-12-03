import os


async def pid(hub):
    return os.getpid()


async def ret_true(hub):
    return True
