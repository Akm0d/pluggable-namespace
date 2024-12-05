async def pre(hub, ctx):
    print("rc_sub1-recursive-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["rc_sub1-recursive-pre"]


async def post(hub, ctx):
    print("rc_sub1-recursive-post")
    ctx.ret.append("rc_sub1-recursive-post")


async def call(hub, ctx):
    print("rc_sub1-recursive-pre-call")
    result = ctx.extra + [
        "rc_sub1-recursive-pre-call",
        await ctx.func(hub=hub),
        "rc_sub1-recursive-post-call",
    ]
    print("rc_sub1-recursive-post-call")
    return result
