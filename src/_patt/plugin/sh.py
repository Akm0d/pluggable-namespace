"""
# SH Pattern

The SH pattern can be extremely useful, it allows you to easily shell out to commands
as an extension of the hub, many projects implement it on `hub.sh`.

## Adding to the hub

Adding the sh sub to the hub is a one line operation

```python
await hub.patt.sh.add_sub()
```

The sub `hub.sh` is now available

## Calling Shell Commands

The command to execute is the first ref on the `sh` sub. To call the `ls` command
without any options simply call `hub.sh.`

```python
stdout = await hub.sh.ls()
```

Arguments to pass to the command can be passed as arguments

```python
stdout = await hub.sh.ls("-l", "-h")
```

A number of modifiers also exist allowing you to get stderr, read the json pumped out
from a command, show the output on the command line and don't capture it, etc.

```python
# Read in the json dumped by the command
json_stdout = await hub.sh.lsblk.json("-J")
# Get the stderr
stderr = await hub.sh.lsblk.stderr("--garbage")
# Show the output on the comamnd line
await hub.sh.lsblk.show()
# Iterate over the lines returned from a command
async for line in hub.sh.ls.lines():
    print(line)
```

"""


async def add_sub(hub, subname="sh", sub=None):
    """
    The sh sub allows for shell commands to be executed right on the hub based on the
    hub reference and then the arguments are passed as args

    Args:
        subname (str): The name of the sub to set as the shell sub, defaults to "sh"
            which places the sub at `hub.sh`
        sub: The sub location to place the shell sub, defaults to placing the sub
            directly on the hub
    """

    class SH:
        def __init__(self):
            self._subname = subname

        def __getattr__(self, name):
            refs = [name]
            return SHNode(refs)

        def __getitem__(self, item: str):
            return getattr(self, str(item))

        # def __setattr__(self, name, value):
        #    # Don't permit attributes to be stored on the SH sub
        #    raise Exception()

    class SHNode:
        def __init__(self, refs):
            self.__dict__["_refs"] = refs

        # def __setattr__(self, name, value):
        #    # Don't permit attributes to be stored on the SH sub
        #    raise Exception()

        def __getattr__(self, name):
            return SHNode([*self._refs, name])

        def __getitem__(self, item: str):
            return getattr(self, str(item))

        async def __call__(self, *args, **kwargs):
            """
            Shell out to the reference
            """
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs
            )
            ret = await proc.communicate()
            return ret[0].decode("utf-8")

        async def lines(self, *args, **kwargs):
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs
            )
            while proc.returncode is None:
                yield (await proc.stdout.readline()).decode("utf-8")
                with hub.lib.contextlib.suppress(hub.lib.asyncio.TimeoutError):
                    await hub.lib.asyncio.wait_for(proc.wait(), 1e-6)

        async def json(self, *args, **kwargs):
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs
            )
            ret = await proc.communicate()
            return hub.lib.json.loads(ret[0].decode("utf-8"))

        async def xml(self, *args, **kwargs):
            """
            Parse the output as xml and return a python dict
            """
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs,
            )
            ret = await proc.communicate()
            return hub.lib.xmltodict.parse(ret[0].decode("utf-8"))

        async def stdout(self, *args, **kwargs):
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs,
            )
            ret = await proc.communicate()
            return ret[0].decode("utf-8")

        async def stderr(self, *args, **kwargs):
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs,
            )
            ret = await proc.communicate()
            return ret[1].decode("utf-8")

        async def raw(self, *args, **kwargs):
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs,
            )
            return await proc.communicate()

        async def plain(self, *args, **kwargs):
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(
                cmd,
                *args,
                stdout=hub.lib.asyncio.subprocess.PIPE,
                stderr=hub.lib.asyncio.subprocess.PIPE,
                **kwargs,
            )
            ret = await proc.communicate()
            log = "STDOUT:\n"
            log += ret[0].decode()
            log += "\nSTDERR:\n"
            log += ret[1].decode()
            return log

        async def show(self, *args, **kwargs):
            """
            Run the commend but don't redirect stdout/stderr
            """
            cmd = self._refs[0]
            proc = await hub.lib.asyncio.create_subprocess_exec(cmd, *args, **kwargs)
            await proc.communicate()

        async def avail(self):
            cmd = self._refs[0]
            return bool(hub.lib.shutil.which(cmd))

        async def which(self):
            cmd = self._refs[0]
            return hub.lib.shutil.which(cmd)

    root = sub or hub
    root._subs[subname] = SH()
