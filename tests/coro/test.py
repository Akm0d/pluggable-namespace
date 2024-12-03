async def simple(hub):
    return True


async def gen(hub):
    for i in range(10):
        yield i
