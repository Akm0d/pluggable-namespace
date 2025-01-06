async def pre(hub, ctx):
    print("dunder-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["dunder-pre"]


async def post(hub, ctx):
    print("dunder-post")
    ctx.ret.append("dunder-post")


async def call(hub, ctx):
    print("dunder-pre-call")
    result = ctx.extra + [
        "dunder-pre-call",
        await ctx.func(hub=hub),
        "dunder-post-call",
    ]
    print("dunder-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("dunder-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["dunder-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("dunder-post-test-fn")
    ctx.ret.append("dunder-post-test-fn")


async def call_test_fn(hub, ctx):
    print("dunder-pre-call-test-fn")
    result = ctx.extra + [
        "dunder-pre-call-test-fn",
        await ctx.func(hub=hub),
        "dunder-post-call-test-fn",
    ]
    print("dunder-post-call-test-fn")
    return result
