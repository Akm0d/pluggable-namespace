async def pre(hub, ctx):
    print("thing-pre")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["thing-pre"]


async def post(hub, ctx):
    print("thing-post")
    ctx.ret.append("thing-post")


async def call(hub, ctx):
    print("thing-pre-call")
    result = ctx.extra + ["thing-pre-call", await ctx.func(hub=hub), "thing-post-call"]
    print("thing-post-call")
    return result


async def pre_test_fn(hub, ctx):
    print("thing-pre-test-fn")
    ctx.extra = (getattr(ctx, "extra", None) or []) + ["thing-pre-test-fn"]


async def post_test_fn(hub, ctx):
    print("thing-post-test-fn")
    ctx.ret.append("thing-post-test-fn")


async def call_test_fn(hub, ctx):
    print("thing-pre-call-test-fn")
    result = ctx.extra + [
        "thing-pre-call-test-fn",
        await ctx.func(hub=hub),
        "thing-post-call-test-fn",
    ]
    print("thing-post-call-test-fn")
    return result
