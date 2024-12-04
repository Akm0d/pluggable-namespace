__virtualname__ = "json"


async def render(hub, data):
    """
    Render the given json data
    """
    try:
        if isinstance(data, str | bytes | bytearray):
            ret = hub.lib.json.loads(data)
        else:
            ret = hub.lib.json.load(data)
    except hub.lib.json.decoder.JSONDecodeError as exc:
        if exc.msg and hasattr(exc, "lineno") and hasattr(exc, "colno"):
            problem = f"{exc.msg} on line: {exc.lineno} column: {exc.colno}"
        else:
            problem = exc.msg
        msg = f"Json render error: {problem}"
        raise hub.exc.rend.RenderError(msg) from exc
    return ret
