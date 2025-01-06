async def func1(hub):
    raise Exception("Pre Contract did not fail")


async def func2(hub):
    raise Exception("Pre Contract did not fail")


async def afunc1(hub):
    raise Exception("Pre Contract did not fail")


async def afunc2(hub):
    raise Exception("Pre Contract did not fail")


async def gen1(hub):
    if True:
        raise Exception("Pre Contract did not fail")
    else:
        yield


async def gen2(hub):
    if True:
        raise Exception("Pre Contract did not fail")
    else:
        yield


async def agen1(hub):
    if True:
        raise Exception("Pre Contract did not fail")
    else:
        yield


async def agen2(hub):
    if True:
        raise Exception("Pre Contract did not fail")
    else:
        yield
