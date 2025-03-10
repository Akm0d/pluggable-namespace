async def setup():

    path = hub.lib.pathlib.Path(log_file).expanduser()
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    log_file = str(path)
