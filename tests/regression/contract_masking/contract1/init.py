async def post(hub, ctx):
    ctx.ret.append("contract1")
    return ctx.ret
