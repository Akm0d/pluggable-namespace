"""
Example contract
"""

__virtualname__ = "test"


async def functions(hub):
    """
    Return the functions
    """
    return ("ping", "demo")


async def pre_ping(hub, ctx):
    """ """
    if len(ctx.args) != 1:
        raise ValueError("ping does not take args!")
    if ctx.kwargs:
        raise ValueError("ping does not take kwargs!")


async def call_ping(hub, ctx):
    """ """
    print("calling!")
    return await ctx.func(*ctx.args, **ctx.kwargs)


async def post_ping(hub, ctx):
    """ """
    print("Calling Post!")
    if not isinstance(ctx.return_value, dict):
        raise ValueError("MUST BE DICT!!")
