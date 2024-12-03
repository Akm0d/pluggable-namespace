async def pre(hub, ctx):
    print("default-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["default-pre"]


async def post(hub, ctx):
    print("default-post")
    ctx.ret.append("default-post")


async def call(hub, ctx):
    print("default-pre-call")
    result = ctx.extra + [
        "default-pre-call",
        await ctx.func(hub=hub),
        "default-post-call",
    ]
    print("default-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("default-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["default-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("default-post-test-fn")
    ctx.ret.append("default-post-test-fn")


async def call_test_fn(hub, ctx):
    print("default-pre-call-test-fn")
    result = ctx.extra + [
        "default-pre-call-test-fn",
        await ctx.func(hub=hub),
        "default-post-call-test-fn",
    ]
    print("default-post-call-test-fn")
    return result
