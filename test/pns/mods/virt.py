async def __virtual__(hub):
    """ """
    try:
        hub.opts  # pylint: disable=undefined-variable
    except Exception:  # pylint: disable=broad-except
        return False
    return True


async def present(hub):
    return True
