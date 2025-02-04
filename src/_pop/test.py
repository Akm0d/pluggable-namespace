"""
Plugin Oriented Programming (POP) hub.

This module provides functions that serve as examples of how to utilize the hub's CLI for testing and benchmarking.
It includes a set of simple functions that can be invoked from the CLI to perform tasks like raising exceptions,
running benchmarks, and calculating Fibonacci sequences. These are primarily for educational and testing purposes
to help new users understand how to interact with and extend the hub's capabilities.
"""

__func_alias__ = {"raise_": "raise"}


async def func(hub, *args, **kwargs):
    """
    A simple function that returns the arguments and keyword arguments passed to it.

    This function is designed for demonstration purposes to show how arguments are passed through the hub CLI.

    Parameters:
        hub (pns.hub.Hub): The hub instance.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        tuple: A tuple containing the list of positional arguments and a dictionary of keyword arguments.
    """
    return args, kwargs


class TestError(Exception): ...


def nest(hub):
    hub._.foo()


def foo(hub):
    hub._.bar()


def bar(hub):
    hub._.baz()


def baz(hub):
    raise TestError("")


async def raise_(hub, message: str = ""):
    """
    Raises a custom exception with an optional message.

    This function is used for testing error handling mechanisms within the hub.

    Parameters:
        hub (pns.hub.Hub): The hub instance.
        message (str, optional): The message to include in the exception.

    Raises:
        TestError: An exception with the provided message.
    """
    raise TestError(message)


async def benchmark(hub, depth=5, width=10000):
    """
    Executes a benchmark test by creating a large number of nested subsystems.

    This function measures the performance of the hub when handling a large structure of nested subs,
    which can be useful for identifying performance bottlenecks and testing scalability.

    Run a pluggable-namespace with all the strict contract checking

    .. code-block:: bash

        python -m hub pns.test.benchmark

    Run an optimized pns

    .. code-block:: bash

        python -O -m hub pns.test.benchmark
    """
    await hub.log.debug("Started Benchmark")
    start_time = hub.lib.time.time()
    for w in range(int(width)):
        name = f"sub_{w}"
        await hub.pop.sub.add(name=name)
        dyne = hub[name]
        for d in range(int(depth)):
            nest_name = f"sub_{d}_{d}"
            await hub.pop.sub.add(name=nest_name, sub=dyne)
            dyne = dyne[nest_name]
    end_time = hub.lib.time.time()
    return f"Total time taken: {end_time - start_time:.2f} seconds."


async def fibonacci(hub, n: int) -> str:
    """
    Computes the nth Fibonacci number using a simple recursive method.

    This function serves as a computational example, primarily for demonstrating recursive function calls.

    Parameters:
        hub (pns.hub.Hub): The hub instance.
        n (int): The position in the Fibonacci sequence to compute.

    Returns:
        int: The nth Fibonacci number.
    """
    n = int(n)
    if n <= 1:
        return str(n)
    else:
        return str(
            await hub.pop.test.fibonacci(n - 1) + await hub.pop.test.fibonacci(n - 2)
        )
