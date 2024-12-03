async def caller(hub):
    # call a reverse sub
    return await hub.fork.foo.bar()
