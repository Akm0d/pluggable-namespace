import asyncio
import inspect

# TODO We need dynamic definition of contract types
TYPE = [
    "sig",
    "pre",
    "call",
    "post",
]

class ContractedContext:
    """
    Contracted function calling context
    """

    def __init__(
        self,
        func: object,
        args: tuple,
        kwargs: dict,
        signature: object,
        ref: str,
        name: str,
        ret=None,
        cache=None,
    ):
        if cache is None:
            cache = {}
        self.func = func
        self.args = list(args)
        self.kwargs = kwargs
        self.signature = signature
        self.ref = ref
        self.__name__ = name
        self.ret = ret
        self.__cache = cache

    @property
    def signature(self):
        return self.signature

    @property
    def cache(self):
        return self.__cache

    def get_arguments(self):
        """
        Return a dictionary of all arguments that will be passed to the function and their
        values, including default arguments.
        """
        if "__bound_signature__" not in self.__cache:
            self.__cache["__bound_signature__"] = self.signature.bind(
                *self.args, **self.kwargs
            )
            # Apply any default values from the signature
            self.__cache["__bound_signature__"].apply_defaults()
        return self.__cache["__bound_signature__"].arguments



# TODO this can be a subclass of Namespace
class Contracted:
    """
    This class wraps functions that have a contract associated with them
    and executes the contract routines
    """

    def __init__(
        self,
        hub,
        contracts: list,
        func: object,
        ref: str,
        name: str,
        parent: object,
        implicit_hub: bool = True,
    ):
        self.__name__ = name
        self.__wrapped__ = func
        self._sig_errors = []
        self.contracts = contracts or []
        self.parent = parent
        self.func = func
        self.hub = hub
        self.implicit_hub = implicit_hub
        self.ref = ref + "." + name
        self._load_contracts()

    @property
    def __doc__(self):
        return self.func.__doc__

    @property
    def __(self):
        return self.parent

    @property
    def signature(self):
        return inspect.signature(self.func)

    @property
    def __dict__(self):
        return self.func.__dict__

    def _get_contracts_by_type(self, contract_type: str):
        matches = []
        fn_contract_name = f"{contract_type}_{self.__name__}"
        for contract in self.contracts:
            if hasattr(contract, fn_contract_name):
                matches.append(getattr(contract, fn_contract_name))
            if hasattr(contract, contract_type):
                matches.append(getattr(contract, contract_type))
        if contract_type == "post":
            matches.reverse()
        return matches

    def _load_contracts(self):
        self.contract_functions = {
            # TODO have these be defined in a module that could be extended
            "pre": self._get_contracts_by_type("pre"),
            "call": self._get_contracts_by_type("call")[:1],
            "post": self._get_contracts_by_type("post"),
        }
        self._has_contracts = (
            sum(len(funcs) for funcs in self.contract_functions.values()) > 0
        )

    async def __call__(self, *args, **kwargs):
        with CallStack(self):
            if self.implicit_hub:
                args = (self.hub,) + args
            if not self._has_contracts:
                ret = self.func(*args, **kwargs)
                if asyncio.iscoroutine(ret):
                    ret = await ret
                return ret
            contract_context = ContractedContext(
                self.func, args, kwargs, self.signature, self.ref, self.__name__
            )
            for fn in self.contract_functions["pre"]:
                pre_ret = await fn(contract_context)
                await self.hub.pns.contract.process_pre_result(pre_ret, fn, self)
            if self.contract_functions["call"]:
                ret = self.contract_functions["call"][0](contract_context)
            else:
                ret = self.func(*contract_context.args, **contract_context.kwargs)
            if asyncio.iscoroutine(ret):
                ret = await ret
            for fn in self.contract_functions["post"]:
                contract_context.ret = ret
                post_ret = await fn(contract_context)
                if post_ret is not None:
                    ret = post_ret
            return ret

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.ref}>"


# TODO does this really need to be a separate contract type?
class ContractedAsyncGen(Contracted):
    async def __call__(self, *args, **kwargs):
        async with CallStack(self):
            if self.implicit_hub:
                args = (self.hub,) + args
            if not self._has_contracts:
                async for chunk in self.func(*args, **kwargs):
                    yield chunk
                return
            contract_context = ContractedContext(
                self.func, args, kwargs, self.signature, self.ref, self.__name__
            )
            for fn in self.contract_functions["pre"]:
                pre_ret = await fn(contract_context)
                await self.hub.pns.contract.process_pre_result(pre_ret, fn, self)
            chunk = None
            if self.contract_functions["call"]:
                async for chunk in self.contract_functions["call"][0](contract_context):
                    yield chunk
            else:
                async for chunk in self.func(
                    *contract_context.args, **contract_context.kwargs
                ):
                    yield chunk
            ret = chunk
            for fn in self.contract_functions["post"]:
                contract_context.ret = ret
                post_ret = await fn(contract_context)
                if post_ret is not None:
                    ret = post_ret


class CallStack:
    """
    A wrapper for functions to add and remove their context from the stack securely
    """
    def __init__(self, contract: Contracted):
        self.contract = contract
        self.last_ref = None
        self.last_call = None

    def __enter__(self):
        self.last_ref = self.contract.hub._last_ref
        self.last_call = self.contract.hub._last_call
        self.contract.hub._last_ref = self.contract.ref
        self.contract.hub._last_call = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.contract.hub._last_ref = self.last_ref
        self.contract.hub._last_call = self.last_call
        self.last_ref = None
        self.last_call = self
