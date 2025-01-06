async def pre(hub, ctx):
    print("recursive-dunder-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-dunder-pre"]


async def post(hub, ctx):
    print("recursive-dunder-post")
    ctx.ret.append("recursive-dunder-post")


async def call(hub, ctx):
    print("recursive-dunder-pre-call")
    result = ctx.extra + [
        "recursive-dunder-pre-call",
        await ctx.func(hub=hub),
        "recursive-dunder-post-call",
    ]
    print("recursive-dunder-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("recursive-dunder-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-dunder-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("recursive-dunder-post-test-fn")
    ctx.ret.append("recursive-dunder-post-test-fn")


async def call_test_fn(hub, ctx):
    print("recursive-dunder-pre-call-test-fn")
    result = ctx.extra + [
        "recursive-dunder-pre-call-test-fn",
        await ctx.func(hub=hub),
        "recursive-dunder-post-call-test-fn",
    ]
    print("recursive-dunder-post-call-test-fn")
    return result
