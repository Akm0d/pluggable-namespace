from collections.abc import Callable

import pns.exc


async def process_pre_result(
    hub,
    pre_ret,
    pre: Callable,
    cn,
):
    if pre_ret is None:
        return

    if isinstance(pre_ret, bool):
        status = pre_ret
        msg = None

    if isinstance(pre_ret, tuple):
        status, msg = pre_ret

    if not msg:
        msg = f"Pre contract '{pre.__name__}' failed for function '{cn.func.__name__}'"

    # If the return of "pre" is "False" then raise an error
    if status is False:
        raise pns.exc.PreContractFailed(msg)
