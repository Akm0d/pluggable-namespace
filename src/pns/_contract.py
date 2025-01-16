import pns.data
import enum
from collections.abc import Callable
from collections import defaultdict


class Context:
    """
    Holds the function context: arguments, signature, and return value.
    This is passed to each contract in the chain as the "ctx" parameter.
    """

    def __init__(self, hub, __func__: Callable, *args, **kwargs):
        self.func = __func__
        self.args = [hub, *args]
        self.kwargs = kwargs
        self.cache = {}
        self.return_value = None


class ContractType(enum.Enum):
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
    This class wraps functions that have a contract associated with them
    and executes the contract routines
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

    async def __call__(self, *args, **kwargs):
        """
        Call the underlying function and execute its contracts in the following order:

        pre -> call -> post
        """
        async with CallStack(self):
            hub = self._
            ctx = Context(hub, self.func, *args, **kwargs)

            for contract in self.contracts[ContractType.PRE]:
                await contract(ctx)

            for contract in self.contracts[ContractType.CALL]:
                ctx.return_value = await contract(ctx)
                break
            else:
                ctx.return_value = await ctx.func(*ctx.args, **ctx.kwargs)

            for contract in reversed(self.contracts[ContractType.POST]):
                ctx.return_value = await contract(ctx)

            return ctx.return_value


class CallStack:
    """
    A wrapper for functions to add and remove their context from the stack securely.
    This allows the hub to keep track of the last function called and the last reference.
    This enables "hub._" to reference the current module from within function calls.
    """

    def __init__(self, contract: Contracted):
        self.contract = contract
        self.hub = self.contract._
        self.last_ref = None
        self.last_call = None

    async def __aenter__(self):
        self.last_ref = self.hub._last_ref
        self.last_call = self.hub._last_call
        self.hub._last_ref = self.contract.__ref__
        self.hub._last_call = self

    async def __aexit__(self, *args):
        self.hub._last_ref = self.last_ref
        self.hub._last_call = self.last_call
        self.last_ref = None
        self.last_call = self
