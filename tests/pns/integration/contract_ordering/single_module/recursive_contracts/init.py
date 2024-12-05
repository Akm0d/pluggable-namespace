async def pre(hub, ctx):
    print("recursive-init-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-init-pre"]


async def post(hub, ctx):
    print("recursive-init-post")
    ctx.ret.append("recursive-init-post")


async def call(hub, ctx):
    print("recursive-init-pre-call")
    result = ctx.extra + [
        "recursive-init-pre-call",
        await ctx.func(hub=hub),
        "recursive-init-post-call",
    ]
    print("recursive-init-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("recursive-init-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["recursive-init-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("recursive-init-post-test-fn")
    ctx.ret.append("recursive-init-post-test-fn")


async def call_test_fn(hub, ctx):
    print("recursive-init-pre-call-test-fn")
    result = ctx.extra + [
        "recursive-init-pre-call-test-fn",
        await ctx.func(hub=hub),
        "recursive-init-post-call-test-fn",
    ]
    print("recursive-init-post-call-test-fn")
    return result
