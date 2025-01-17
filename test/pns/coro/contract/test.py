async def pre(hub, ctx):
    hub.PRE = True


async def post(hub, ctx):
    hub.POST = True
    return ctx.return_value
