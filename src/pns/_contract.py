"""
Implements the contract system for enforcing interfaces and behaviors in a dynamic namespace system.

This module defines the core components for the contract system used in a plugin-oriented architecture. Contracts
are mechanisms that enforce predefined rules or behaviors on functions, ensuring that plugins adhere to specified
interfaces and allowing for pre and post conditions to be applied to function calls. The system supports signature
enforcement, wrapping functions with pre, post, and call behaviors, and allowing recursive application of behaviors
to entire namespaces.

Classes:
    - Context: Manages the function execution context, providing access to arguments, return values, and a cache.
    - ContractType: Enumerates the types of contracts and provides utilities to associate functions with contract types.
    - Contracted: A dynamic namespace wrapper that manages the execution of associated contracts.
    - CallStack: Manages the execution stack for contracted functions, ensuring context integrity across calls.

The contract system is integral to maintaining consistency and enforcing security and operational policies across
modular components in complex systems. It is particularly suited to applications where components are loaded dynamically
and need to interact seamlessly while adhering to strict operational protocols.
"""

import pns.data
import enum
import inspect
from collections.abc import Callable
from collections import defaultdict
from collections.abc import AsyncGenerator


class Context:
    """
    Represents the context of a function call within the contract system, encapsulating all necessary execution data.

    This context is passed to each contract in the chain, allowing contract functions to access and modify the execution
    state, arguments, keyword arguments, and the return value of the function call.

    Attributes:
        func (Callable): The function to be executed.
        args (list): The arguments passed to the function.
        kwargs (dict): The keyword arguments passed to the function.
        cache (dict): A cache used to store data that might be reused during the function call lifecycle.
        return_value (any): The value returned by the function, which can be modified by post contracts.
    """

    def __init__(
        self, hub, __func__: Callable, __parent__: "Contracted", *args, **kwargs
    ):
        self.func = __func__
        self.__ = __parent__
        # Implicitly add the hub as the first argument of the Contracted call
        self.args = [hub, *args]
        self.kwargs = kwargs
        self.cache = {}
        self.return_value = None


class ContractType(enum.Enum):
    """
    Enumerates the types of contracts that can be applied to functions within the namespace.

    Each member of the enum represents a different type of contract that can be applied:
    - SIG: Signature enforcement contracts.
    - PRE: Pre-execution contracts.
    - CALL: Replacement or wrapper for the actual function call.
    - POST: Post-execution contracts.
    - Recursive variants of the above for applying to all descendants in the namespace.

    Methods:
        recursive: Property that indicates if the contract type applies recursively to nested sub-modules
        from_func: Class method that determines the contract type from a function name.
    """

    SIG = "sig"
    PRE = "pre"
    CALL = "call"
    POST = "post"
    R_SIG = "r_sig"
    R_PRE = "r_pre"
    R_CALL = "r_call"
    R_POST = "r_post"

    @property
    def recursive(self) -> bool:
        """
        Recursive contracts apply to every Namespace underneath the one where they are defined
        """
        return self.value.startswith("r_")

    @classmethod
    def from_func(cls, func: Callable):
        """
        Inspect the function name and assign it the appropriate contract type.
        """
        name = func.__name__

        # Try to match the remaining portion
        for ctype in cls:
            if (ctype.value == name) or name.startswith(f"{ctype.value}_"):
                return ctype


class Contracted(pns.data.Namespace):
    """
    Wraps functions with contracts, managing the execution of these contracts according to their type.

    This class acts as a container for contracted functions, ensuring that any associated contracts are executed
    in the correct order and that the function context is managed appropriately.

    Attributes:
        func (Callable): The wrapped function.
        contracts (dict): A mapping of contract types to lists of callables representing the contracts.

    Methods:
        __call__: Asynchronously executes the wrapped function along with its contracts.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        contracts: dict[ContractType, list[Callable]] = None,
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        self.func = func
        self.contracts = contracts or defaultdict(list)

    def __new__(cls, name: str, func: Callable, contracts=None, **kwargs):
        """
        Decide between different subclasses based on the function type
        """
        if inspect.isasyncgenfunction(func):
            return super().__new__(ContractedGen)
        else:
            return super().__new__(Contracted)

    async def __gen_ctx__(self, *args, **kwargs):
        """
        Create and prepare the function context, executing pre-call contracts.
        """
        hub = self._
        ctx = Context(hub, self.func, self, *args, **kwargs)

        # Pre contracts are used to validate/modify args and kwargs in the ctx
        await self.__call_pre__(ctx)
        return ctx

    async def __call_pre__(self, ctx):
        """
        Execute all pre-call contracts.
        """
        pre_contracts = (
            self.contracts[ContractType.PRE] + self.contracts[ContractType.R_PRE]
        )
        for pre_contract in pre_contracts:
            await pre_contract(ctx)

    async def __call_post__(self, ctx):
        """
        Execute all post-call contracts in reverse order.
        """
        post_contracts = (
            self.contracts[ContractType.POST] + self.contracts[ContractType.R_POST]
        )
        for post_contract in reversed(post_contracts):
            ctx.return_value = await post_contract(ctx)

    async def __call__(self, *args, **kwargs):
        """
        Handle the execution of the wrapped function.
        """
        async with CallStack(self):
            ctx = await self.__gen_ctx__(*args, **kwargs)
            call_contracts = (
                self.contracts[ContractType.CALL] + self.contracts[ContractType.R_CALL]
            )
            for call_contract in call_contracts:
                ctx.return_value = await call_contract(ctx)
                # Only call the first call contract
                break
            else:
                # If there was no call contract, then call the function directly
                ctx.return_value = await ctx.func(*ctx.args, **ctx.kwargs)

            await self.__call_post__(ctx)

            return ctx.return_value


class ContractedGen(Contracted):
    """
    Specialized subclass for async generator functions.
    """

    async def __call__(self, *args, **kwargs) -> AsyncGenerator:
        """
        Handle the wrapped function for async generator functions.
        """
        async with CallStack(self):
            ctx = await self.__gen_ctx__(*args, **kwargs)

            call_contracts = (
                self.contracts[ContractType.CALL] + self.contracts[ContractType.R_CALL]
            )
            for call_contract in call_contracts:
                coro_gen = call_contract(ctx)
                # Only call the first call contract
                break
            else:
                # If there was no call contract, then call the function directly
                coro_gen = ctx.func(*ctx.args, **ctx.kwargs)

            async for result in coro_gen:
                ctx.return_value = result
                # Apply post contracts ot every value in the reuslt
                await self.__call_post__(ctx)
                yield ctx.return_value


class CallStack:
    """
    Manages the stack context for contracted functions, ensuring that the function's execution context is restored after a call.

    This class is used to push and pop function contexts from a stack, maintaining a reference to the current and last executed function. This is particularly useful in systems where understanding the flow of function calls is necessary, such as in detailed debugging or logging.

    Attributes:
        contract (Contracted): The contracted function currently being managed.
        hub (Namespace): The namespace object representing the current hub.
        last_ref (str): The reference to the last function called.
        last_call (any): The last executed function call context.
    """

    def __init__(self, contract: Contracted):
        self.contract = contract
        self.hub = self.contract._
        self.last_ref = None
        self.last_call = None

    async def __aenter__(self):
        """Enters the function call context, setting up references to manage the call stack."""
        self.last_ref = self.hub._last_ref
        self.last_call = self.hub._last_call
        self.hub._last_ref = self.contract.__ref__
        self.hub._last_call = self

    async def __aexit__(self, *args):
        """Exits the function call context, restoring the previous function context."""
        self.hub._last_ref = self.last_ref
        self.hub._last_call = self.last_call
        self.last_ref = None
        self.last_call = None
