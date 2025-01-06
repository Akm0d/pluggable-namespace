__virtualname__ = "priv"


async def call(hub, ctx):
    return await ctx.func(*ctx.args, **ctx.kwargs)
