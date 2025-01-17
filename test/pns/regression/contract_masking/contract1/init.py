async def post(hub, ctx):
    ctx.return_value.append("contract1")
    return ctx.return_value
