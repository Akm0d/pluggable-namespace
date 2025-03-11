def __virtual__(hub):
    return "aioconsole" in hub.lib, "Missing aioconsole library"


async def process(hub, msg: str):
    await hub.lib.aioconsole.aprint(msg, file=hub.lib.sys.stderr)
