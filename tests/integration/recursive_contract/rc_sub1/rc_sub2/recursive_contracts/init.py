async def pre_test_call(hub, ctx):
    print("rc_sub2-recursive-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["rc_sub2-recursive-pre"]


async def post_test_call(hub, ctx):
    print("rc_sub2-recursive-post")
    ctx.ret.append("rc_sub2-recursive-post")


async def call(hub, ctx):
    print("rc_sub2-recursive-pre-call")
    result = ctx.extra + [
        "rc_sub2-recursive-pre-call",
        await ctx.func(hub=hub),
        "rc_sub2-recursive-post-call",
    ]
    print("rc_sub2-recursive-post-call")
    return result
