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
        self.args = (hub, *args)
        self.kwargs = kwargs
        self.return_value = None


class ContractType(enum.Enum):
    SIG = "sig"
    PRE = "pre"
    CALL = "call"
    POST = "post"
    RECURSIVE = "r"

    @classmethod
    def new(cls, func: Callable):
        """
        Inspect the function name and assign it the appropriate contract type
        """
        name = func.__name__
        for contract_type in cls:
            if name == contract_type.value or name.startswith(
                contract_type.value + "_"
            ):
                return contract_type


class Contracted(pns.data.Namespace):
    """
    This class wraps functions that have a contract associated with them
    and executes the contract routines
    """

    def __init__(
        self, name: str, func: Callable, contracts: list[Callable] = (), **kwargs
    ):
        super().__init__(name, **kwargs)
        self.func = func
        self.contracts = defaultdict(list)
        for contract in contracts:
            self.add_contract(contract)

    def add_contract(self, function: callable):
        """
        Add a contract to the function
        """
        contract_type = ContractType.new(function)
        if contract_type:
            self.contracts[contract_type].append(function)

    async def __call__(self, *args, **kwargs):
        """
        Call the underlying function and execute its contracts in the following order:

        pre -> call -> post
        """
        async with CallStack(self):
            hub = self._
            ctx = Context(hub, self.func, *args, **kwargs)

            for contract in self.contracts[ContractType.PRE]:
                await contract(hub, ctx)

            for contract in self.contracts[ContractType.CALL]:
                ctx.return_value = await contract(hub, ctx)
            else:
                ctx.return_value = await ctx.func(*ctx.args, **ctx.kwargs)

            for contract in reversed(self.contracts[ContractType.POST]):
                ctx.return_value = await contract(hub, ctx)

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
