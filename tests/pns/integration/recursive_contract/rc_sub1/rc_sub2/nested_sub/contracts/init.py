async def pre(hub, ctx):
    print("regular-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["regular-pre"]


async def post(hub, ctx):
    print("regular-post")
    ctx.ret.append("regular-post")


async def call(hub, ctx):
    print("regular-pre-call")
    result = ctx.extra + ["regular-pre-call", ctx.func(hub=hub), "regular-post-call"]
    print("regular-post-call")
    return result
