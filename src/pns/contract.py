from ._debug import DEBUG_PNS_GETATTR
from collections.abc import Callable
from collections import defaultdict

if DEBUG_PNS_GETATTR:
    from pns._contract import Contracted, ContractType
else:
    from pns._ccontract import Contracted, ContractType


CONTRACTS = "__contracts__"

def recurse(loaded_mod: "pns.mod.LoadedMod") -> dict[ContractType, list[Callable]]:
    """
    Recurse the parents of the loaded_mod and collect the contracts and recursive contracts
    """
    contracts = defaultdict[list]
    current = loaded_mod
    while current:
        for func in current.contract._funcs.values():
            contract_type = ContractType.from_func(func)
            if not contract_type:
                continue
            contracts[contract_type].append(func)
        
        current = current.__
        
    return contracts