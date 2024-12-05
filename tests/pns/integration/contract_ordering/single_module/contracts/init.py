async def pre(hub, ctx):
    print("init-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["init-pre"]


async def post(hub, ctx):
    print("init-post")
    ctx.ret.append("init-post")


async def call(hub, ctx):
    print("init-pre-call")
    result = ctx.extra + ["init-pre-call", await ctx.func(hub=hub), "init-post-call"]
    print("init-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("init-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["init-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("init-post-test-fn")
    ctx.ret.append("init-post-test-fn")


async def call_test_fn(hub, ctx):
    print("init-pre-call-test-fn")
    result = ctx.extra + [
        "init-pre-call-test-fn",
        await ctx.func(hub=hub),
        "init-post-call-test-fn",
    ]
    print("init-post-call-test-fn")
    return result
