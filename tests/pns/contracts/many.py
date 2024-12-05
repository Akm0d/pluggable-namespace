__virtualname__ = "all"


async def pre(hub, ctx):
    if len(ctx.args) > 1:
        raise ValueError("No can haz args!")
    if ctx.kwargs:
        raise ValueError("No can haz kwargs!")


async def call(hub, ctx):
    return await ctx.func(*ctx.args, **ctx.kwargs)


async def call_list(hub, ctx):
    return ["override"]


async def post(hub, ctx):
    ret = ctx.ret
    if isinstance(ret, list):
        ret.append("post called")
    elif isinstance(ret, dict):
        ret["post"] = "called"
    return ret
