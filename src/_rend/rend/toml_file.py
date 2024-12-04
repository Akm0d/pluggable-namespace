__virtualname__ = "toml"


async def render(hub, data):
    """
    Render the given toml data
    """
    if isinstance(data, bytes):
        data = data.decode()
    try:
        ret = hub.lib.toml.loads(data)
    except hub.lib.toml.TomlDecodeError as exc:
        if exc.msg and hasattr(exc, "lineno") and hasattr(exc, "colno"):
            problem = f"{exc.msg} on line: {exc.lineno} column: {exc.colno}"
        else:
            problem = exc.msg
        msg = f"Toml render error: {problem}"
        raise hub.exc.rend.RenderError(msg) from exc
    return ret
