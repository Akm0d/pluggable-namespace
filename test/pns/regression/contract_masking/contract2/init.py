async def post(hub, ctx):
    ctx.return_value.append("contract2")
    return ctx.return_value
