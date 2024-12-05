import os


async def ping(hub):
    return {"pid": os.getpid()}


async def aping(hub):
    return {"async pid": os.getpid()}
