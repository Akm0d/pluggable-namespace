async def post(hub, ctx):
    ctx.ret.append("contract2")
    return ctx.ret
