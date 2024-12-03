import asyncio
import inspect
from collections.abc import Iterable
from cpython cimport dict

cdef class ContractedContext:
    """
    Contracted function calling context
    """
    cdef:
        public object func
        public list args
        public dict[str, object] kwargs
        public str ref
        public str __name__
        public object ret
        object signature
        dict[str, object] __cache

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
    def __signature__(self):
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


def load_contract(
    contracts,
    default_contracts: Iterable[str],
    mod: object,
    name: str,
) -> list[object]:
    """
    return a Contract object loaded up
    Dynamically create the correct Contracted type
    :param contracts: Contracts functions to add to the sub
    :param default_contracts: The contracts that have been marked as defaults
    :param mod: A loader module
    :param name: The name of the module to get from the loader
    """
    raws = []
    loaded_contracts = []
    if hasattr(contracts, name):
        loaded_contracts.append(name)
        raws.append(getattr(contracts, name))
    if hasattr(contracts, "init"):
        if "init" not in loaded_contracts:
            loaded_contracts.append("init")
            raws.append(getattr(contracts, "init"))
    if hasattr(mod, "__contracts__"):
        cnames = getattr(mod, "__contracts__")
        for cname in cnames:
            if cname in contracts:
                loaded_contracts.append(cname)
                raws.append(getattr(contracts, cname))
    return raws


cdef class Contracted:
    """
    This class wraps functions that have a contract associated with them
    and executes the contract routines
    """
    cdef:
        public bint _has_contracts
        cdef public bint implicit_hub
        public dict[str, list[object]] contract_functions
        public object hub
        public object func
        public object signature
        cdef public str __name__
        cdef public str ref
        list _sig_errors
        public list contracts
        object __wrapped__
        object parent

    def __init__(
                self,
                hub,
                contracts: list,
                func: object,
                ref: str,
                name: str,
                parent: object,
                implicit_hub: bool = True
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
        # Manually define the function signature if needed
        self.signature = inspect.signature(self.func)

        self._load_contracts()

    @property
    def __doc__(self):
        return self.func.__doc__

    @property
    def __(self):
        return self.parent

    @property
    def __signature__(self):
        return self.signature

    @property
    def __dict__(self):
        return self.func.__dict__

    cdef _get_contracts_by_type(self, contract_type: str):
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

    cdef _load_contracts(self):
        # if Contracted - only allow regular pre/post
        # if ContractedAsync - allow coroutines and functions

        self.contract_functions = {
            "pre": self._get_contracts_by_type("pre"),
            "call": self._get_contracts_by_type("call")[:1],
            "post": self._get_contracts_by_type("post"),
        }
        self._has_contracts = sum(len(funcs) for funcs in self.contract_functions.values()) > 0

    async def __call__(self, *args, **kwargs):
        async with CallStack(self):
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

            # Process pre contracts
            for fn in self.contract_functions["pre"]:
                pre_ret = await fn(contract_context)

                await self.hub.pns.contract.process_pre_result(pre_ret, fn, self)

            # Call the one call contract
            if self.contract_functions["call"]:
                ret = self.contract_functions["call"][0](contract_context)
            else:
                ret = self.func(*contract_context.args, **contract_context.kwargs)

            if asyncio.iscoroutine(ret):
                ret = await ret

            # Handle post contracts
            for fn in self.contract_functions["post"]:
                contract_context.ret = ret
                post_ret = await fn(contract_context)
                if post_ret is not None:
                    ret = post_ret

            return ret

    def __getstate__(self):
        return {
            "ref": self.ref,
            "name": self.__name__,
            "implicit_hub": self.implicit_hub,
            "contracts": self.contracts,
        }

    def __setstate__(self, state: dict[str, object]):
        self.ref = state["ref"]
        self.__name__ = state["name"]
        self.func = self.hub[self.ref][self.__name__].func
        self.implicit_hub = state["implicit_hub"]
        self.contracts = state["contracts"]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.ref}>"


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
        self.ref = contract.ref
        self._last_ref = None
        self._last_call = None

    async def __aenter__(self):
        # Store the previous state
        self._last_ref = self.contract.hub._last_ref
        self._last_call = self.contract.hub._last_call
        # Store this call on the hub as the latest ref
        self.contract.hub._last_ref = self.ref
        self.contract.hub._last_call = self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Restore the previous call as the last one called
        self.contract.hub._last_ref = self._last_ref
        self.contract.hub._last_call = self._last_call
        self._last_ref = None
        self._last_call = self


def create_contracted(
    hub,
    contracts: list["pns.loader.LoadedMod"],
    func,
    ref: str,
    name: str,
    parent: object,
    implicit_hub: bool = True,
) -> Contracted:
    """
    Dynamically create the correct Contracted type
    :param hub: The redistributed pns central hub
    :param contracts: Contracts functions to add to the sub
    :param func: The contracted function to call
    :param ref: The reference to the function on the hub
    :param name: The name of the module to get from the loader
    :param parent: The object on the namespace above this contract
    :param implicit_hub: True if a hub should be implicitly injected into the "call" method
    """
    if inspect.isasyncgenfunction(func):
        return ContractedAsyncGen(hub, contracts, func, ref, name, implicit_hub)
    else:
        return Contracted(hub, contracts, func, ref, name, parent, implicit_hub)
