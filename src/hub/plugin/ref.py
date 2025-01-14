DEFAULT_OUTPUTTER = "yaml"


async def resolve(hub, ref: object, *args, **kwargs) -> object:
    """
    Take an object found on the hub and if it is a function, call it.
    If it is a generator, retrieve all its values.
    As a last resort just return the plain object as is.

    Args:
        hub (pns.hub.Hub): The global namespace
        ref (object): An object found on the hub
    """
    try:
        if (
            hub.lib.asyncio.iscoroutinefunction(ref)
            or isinstance(
                ref, hub.lib.typing.Callable | hub.lib.pns.contract.Contracted
            )
            or callable(ref)
        ):
            # Call the named reference on the hub
            ret = ref(*args, **kwargs)
            # If the return was an Async Generator, then yield all the results
            if hub.lib.inspect.isasyncgen(ret):
                ret = [_ async for _ in ret]
            # If the return was a coroutine then await it
            elif hub.lib.asyncio.iscoroutine(ret):
                ret = await ret
        else:
            # This wasn't a callable function, just return the object on the hub
            ret = ref
    except Exception as e:
        msg = f"Error calling {ref}: {e}"
        await hub.log.error(msg)
        raise ChildProcessError(msg) from e
    return ret


async def output(hub, ret: object):
    """
    Output a serialized version of the given object to the console.

    Args:
        hub (pns.hub.Hub): The global namespace
        ret (object): A resolved object from the hub
    """
    if isinstance(ret, int):
        hub.lib.sys.exit(ret)
    elif isinstance(ret, str):
        await hub.lib.aioconsole.aprint(ret)
    else:
        outputter = hub.OPT.rend.get("output") or DEFAULT_OUTPUTTER
        formatted = await hub.output[outputter].display(ret)
        await hub.lib.aioconsole.aprint(formatted)
