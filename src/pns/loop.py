import asyncio
import functools
import concurrent.futures as fut
import asyncio
import functools
from typing import Any
from collections.abc import Callable


def run(coroutine):
    """
    Run an asynchronous coroutine from synchronous code.

    Parameters:
    - coroutine: The asynchronous coroutine to be run.

    Returns:
    The result of the coroutine if block is True; otherwise, None.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Create a new loop, run the coroutine and return the result
        return asyncio.run(coroutine)

    # Prepare the executor
    with fut.ThreadPoolExecutor() as executor:
        # Submit the coroutine to the executor
        future = executor.submit(functools.partial(asyncio.run, coroutine))
        # Block until the coroutine finishes
        return future.result()


def make_async(
    sync_func: Callable[..., Any], *args, **kwargs
) -> Callable[..., asyncio.Future]:
    """
    Convert a synchronous function into an asynchronous function.

    :param sync_func: The synchronous function to convert.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: An asynchronous function that returns a Future.
    """
    # Create a partially applied version of the function with the given arguments
    partial_func = functools.partial(sync_func, *args, **kwargs)

    # Define an asynchronous wrapper that executes the function using `asyncio.to_thread`
    async def async_wrapper():
        return await asyncio.to_thread(partial_func)

    return async_wrapper
