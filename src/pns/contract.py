from ._debug import DEBUG_PNS_GETATTR
from collections.abc import Callable
from collections import defaultdict

if DEBUG_PNS_GETATTR:
    from pns._contract import Contracted, ContractType
else:
    from pns._ccontract import Contracted, ContractType


CONTRACTS = "__contracts__"


def load(loaded_mod: "pns.mod.LoadedMod") -> dict[ContractType, list[Callable]]:
    """
    Find the contract functions in the module, classify them, and return them in a dictionary
    """
    contracts = defaultdict(list)
    for mod in loaded_mod._mod.values():
        for func in mod._func.values():
            contract_type = ContractType.from_func(func)
            if not contract_type:
                continue
            contracts[contract_type].append(func)
    return contracts


def recurse(loaded_mod: "pns.mod.LoadedMod") -> dict[ContractType, list[Callable]]:
    """
    Recurse the parents of the loaded_mod and collect the contracts and recursive contracts
    """
    contracts = defaultdict(list)
    current = loaded_mod.__

    while current is not None:

        # TODO iterate over the parent subs and add their recursive contracts to this one
        for func in current.contract.values():
            contract_type = ContractType.from_func(func)
            if not contract_type:
                continue
            contracts[contract_type].append(func)

        current = current.__

    return contracts
