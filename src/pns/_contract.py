import pns.data
from collections.abc import Callable

class Contracted(pns.data.Namespace):
    """
    This class wraps functions that have a contract associated with them
    and executes the contract routines
    """
    def __init__(self, name: str, func: Callable, **kwargs):
        super().__init__(name, **kwargs)
        self._func = func

    async def __call__(self, *args, **kwargs):
        async with CallStack(self):
            return await self._func(self._, *args, **kwargs)


class CallStack:
    """
    A wrapper for functions to add and remove their context from the stack securely
    """
    def __init__(self, contract: Contracted):
        self.contract = contract
        self.last_ref = None
        self.last_call = None

    async def __aenter__(self):
        self.last_ref = self.contract._._last_ref
        self.last_call = self.contract._._last_call
        self.contract._._last_ref = self.contract.__ref__
        self.contract._._last_call = self

    async def __aexit__(self, *args):
        self.contract._._last_ref = self.last_ref
        self.contract._._last_call = self.last_call
        self.last_ref = None
        self.last_call = self
