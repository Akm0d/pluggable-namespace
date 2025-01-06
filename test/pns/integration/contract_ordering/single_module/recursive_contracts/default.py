async def pre(hub, ctx):
    print("recursive-default-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-default-pre"]


async def post(hub, ctx):
    print("recursive-default-post")
    ctx.ret.append("recursive-default-post")


async def call(hub, ctx):
    print("recursive-default-pre-call")
    result = ctx.extra + [
        "recursive-default-pre-call",
        await ctx.func(hub=hub),
        "recursive-default-post-call",
    ]
    print("recursive-default-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("recursive-default-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-default-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("recursive-default-post-test-fn")
    ctx.ret.append("recursive-default-post-test-fn")


async def call_test_fn(hub, ctx):
    print("recursive-default-pre-call-test-fn")
    result = ctx.extra + [
        "recursive-default-pre-call-test-fn",
        await ctx.func(hub=hub),
        "recursive-default-post-call-test-fn",
    ]
    print("recursive-default-post-call-test-fn")
    return result
