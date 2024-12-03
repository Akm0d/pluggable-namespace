async def pre(hub, ctx):
    print("recursive-thing-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-thing-pre"]


async def post(hub, ctx):
    print("recursive-thing-post")
    ctx.ret.append("recursive-thing-post")


async def call(hub, ctx):
    print("recursive-thing-pre-call")
    result = ctx.extra + [
        "recursive-thing-pre-call",
        await ctx.func(hub=hub),
        "recursive-thing-post-call",
    ]
    print("recursive-thing-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("recursive-thing-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-thing-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("recursive-thing-post-test-fn")
    ctx.ret.append("recursive-thing-post-test-fn")


async def call_test_fn(hub, ctx):
    print("recursive-thing-pre-call-test-fn")
    result = ctx.extra + [
        "recursive-thing-pre-call-test-fn",
        await ctx.func(hub=hub),
        "recursive-thing-post-call-test-fn",
    ]
    print("recursive-thing-post-call-test-fn")
    return result
