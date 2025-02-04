"""
Provides utilities for integrating synchronous code with asynchronous execution contexts.

This module contains helper functions designed to facilitate the execution of synchronous functions
within an asynchronous environment, and vice versa. It leverages Python's asyncio library to create
and manage event loops, enabling seamless execution of asynchronous coroutines from synchronous contexts
and converting synchronous functions to asynchronous ones.

Functions:
    - run: Executes an asynchronous coroutine synchronously by managing the event loop.
    - make_async: Transforms a synchronous function into an asynchronous function, which can then be executed
        within an asynchronous event loop.

These utilities are crucial for applications that need to bridge traditional synchronous operations with
modern asynchronous programming models, particularly in environments where both styles coexist.
"""

import asyncio
import functools
import concurrent.futures as fut
from typing import Any
from collections.abc import Callable


def run(coroutine):
    """
    Execute an asynchronous coroutine synchronously by managing the asyncio event loop.

    This function checks if an asyncio event loop is already running; if not, it creates a new one
    and runs the given coroutine, ensuring that the coroutine's execution completes before returning.

    Parameters:
        coroutine (coroutine): The asyncio coroutine to be executed.

    Returns:
        Any: The result of the coroutine after its execution.

    Raises:
        RuntimeError: If called from a running event loop and the coroutine could not be executed.
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
    Convert a synchronous function into an asynchronous function using asyncio's threading utilities.

    This function creates a wrapper that, when called, executes the given synchronous function in a separate
    thread managed by asyncio, allowing it to be called within an asyncio event loop without blocking the loop.

    Parameters:
        sync_func (Callable[..., Any]): The synchronous function to convert into an asynchronous one.
        args (tuple): Positional arguments to be passed to the synchronous function.
        kwargs (dict): Keyword arguments to be passed to the synchronous function.

    Returns:
        Callable[..., asyncio.Future]: An asynchronous wrapper around the given synchronous function.
    """
    # Create a partially applied version of the function with the given arguments
    partial_func = functools.partial(sync_func, *args, **kwargs)

    # Define an asynchronous wrapper that executes the function using `asyncio.to_thread`
    async def async_wrapper():
        return await asyncio.to_thread(partial_func)

    return async_wrapper
