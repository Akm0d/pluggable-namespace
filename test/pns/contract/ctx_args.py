"""
Contract Context
"""

__virtualname__ = "ctx_args"


async def call(hub, ctx):
    """ """
    return ctx.get_argument(ctx.get_argument("value"))
