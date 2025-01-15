async def cli(hub):
    if hub.OPT.rend.subs:
        ret = await hub.rend.init.parse_subs(hub.OPT.rend.subs, hub.OPT.rend.pipe)
    else:
        ret = await hub.rend.init.parse(hub.OPT.rend.file, hub.OPT.rend.pipe)
    print(await hub.output.nested.display(ret))


async def render(hub, data, renderer: str):
    # Remove any leftover carriage-returns that may have made it this far
    renderer = renderer.strip()
    data = await hub.rend[renderer].render(data)
    return data


async def parse_subs(hub, subs: list, pipe: str = None) -> dict:
    ret = {}
    for sub in subs:
        for sdir in hub[sub]._dir:
            sdir_path = hub.lib.pathlib.Path(sdir)
            for fn in sdir_path.iterdir():
                if fn.suffix == ".sls":
                    up = await hub.rend.init.parse(str(sdir_path / fn), pipe)
                    ret.update(up)
    return ret


async def parse(hub, fn: str, pipe: str = None) -> str:
    """
    Pass in the render pipe to use to render the given file. If no pipe is
    passed in then the file will be checked for a render shebang line. If
    no render shebang line is present then the system will raise an
    Exception
    If a file defines a shebang render pipe and a pipe is passed in, the
    shebang render pipe line will be used
    """
    path = hub.lib.pathlib.Path(fn).absolute()
    with open(path, "rb") as rfh:
        data = rfh.read()
        data = data.replace(b"\r", b"")
    if data.startswith(b"#!"):
        dpipe = data[2 : data.index(b"\n")].split(b"|")
    elif pipe:
        dpipe = pipe.split("|")
    else:
        msg = f"File {fn} passed in without a render pipe defined"
        raise hub.exc.rend.RendPipeError(msg)
    for renderer in dpipe:
        if isinstance(renderer, bytes):
            str_renderer = renderer.decode()
        else:
            str_renderer = renderer
        str_renderer = str_renderer.strip()
        data = await hub.rend.init.render(data, str_renderer)

    return data


async def parse_bytes(hub, block: dict, pipe: str or bytes = None):
    """
    Send in a block from a render file and render it using the named pipe
    """
    if isinstance(pipe, str):
        pipe = pipe.split("|")
    if isinstance(pipe, bytes):
        pipe = pipe.split(b"|")
    fn = block.get("fn")
    ln = block.get("ln")
    data = block.get("bytes")
    pipe = block.get("pipe", pipe)
    if pipe is None:
        msg = f"File {fn} at block line {ln} passed in without a render pipe defined"
        raise hub.exc.rend.RendPipeError(msg)
    for renderer in pipe:
        if isinstance(renderer, bytes):
            str_renderer = renderer.decode()
        else:
            str_renderer = renderer
        data = await hub.rend.init.render(data, str_renderer)
    return data


async def blocks(hub, fn: str, content: bytes = None):
    """
    Pull the render blocks out of a bytes content along with the render metadata
    stored in shebang lines. If the content is None, it will be populated by reading the file fn.
    """
    pair_length = 2
    bname = "raw"
    ret = {bname: {"ln": 0, "fn": fn, "bytes": b""}}
    bnames = [bname]
    rm_bnames = set()

    if content is None:
        with open(fn, "rb") as rfh:
            content = rfh.read()

    num = -1
    for line in content.splitlines(True):
        num += 1
        if line.startswith(b"#!"):
            # Found metadata tag
            root = line[2:].strip()
            if root == b"END":
                bnames.pop(-1)
                if not bnames:
                    msg = f"Unexpected End of file line {num}"
                    raise hub.exc.rend.RenderError(msg)
                bname = bnames[-1]
                continue
            else:
                bname = f"{fn}|{hub.lib.secrets.token_hex(2)}"
                ret[bname] = {"ln": num, "fn": fn, "keys": {}, "bytes": b""}
                bnames.append(bname)
            parts = root.split(b";")
            for part in parts:
                if b":" in part:
                    req = part.split(b":")
                    if len(req) < pair_length:
                        continue
                    ret[bname]["keys"][req[0].decode()] = req[1].decode()
                else:
                    if b"|" in part:
                        pipes = part.split(b"|")
                    else:
                        pipes = [part]
                    ret[bname]["pipe"] = pipes
        else:
            # Remove carriage returns that may have been added by windows
            ret[bname]["bytes"] += line.replace(b"\r", b"")
    for bname, data in ret.items():
        if not data["bytes"]:
            rm_bnames.add(bname)
    for bname in rm_bnames:
        ret.pop(bname)
    return ret
