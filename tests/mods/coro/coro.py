__virtualname__ = "coro"


try:
    import tornado.gen

    HAS_TORNADO = True
except ImportError:
    HAS_TORNADO = False


async def asyncio_demo(hub):
    return True


if HAS_TORNADO:

    @tornado.gen.coroutine
    def tornado_demo(hub):
        return False
