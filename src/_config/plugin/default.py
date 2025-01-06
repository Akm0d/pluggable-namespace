async def __init__(hub):
    hub._.REF_PATTERN = hub.lib.re.compile(r"^hub\.(\w+(\.\w+)+)\(\)$")


async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Remove 'default' from the argument opts, it will be handled by the config prioritizer, not argparse.
    If the "default" is a function that exists on the hub, then call it to get the default value.
    This allows you to call a function on the hub to do more processing on the default.
    This could be useful for using a different value for the default based on OS.

    I.e.

    config:
      my_app:
        my_opt:
          default: hub.my_sub.mod.func()
    """
    default = opts.pop("default", None)

    if default and isinstance(default, str):
        match = hub._.REF_PATTERN.match(default)
        if match:
            ref = match.group(1)
            func = hub.lib.pns.ref.find(hub, ref)
            default = func()
            if hub.lib.asyncio.iscoroutine(default):
                default = await default

    return {"default": default}
