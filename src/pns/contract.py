from ._debug import DEBUG_PNS_GETATTR
from collections.abc import Callable
from collections import defaultdict
import pns.data

if DEBUG_PNS_GETATTR:
    from pns._contract import Contracted, ContractType
else:
    from pns._ccontract import Contracted, ContractType


CONTRACTS = "__contracts__"


def match(loaded: "pns.mod.Loaded", name: str) -> dict[ContractType, list[Callable]]:
    """
    Recurse the parents of the loaded_mod and collect the contracts and recursive contracts.
    Match them to the current function name and ref
    """
    contracts = defaultdict(list)
    explicit_contracts = getattr(loaded, CONTRACTS, ())
    # Contracts in an "init" module are universal
    matching_mods = {"init", loaded.__name__, *explicit_contracts}

    # Move up the tree until we are on the nearest Sub
    # We will match with the current sub's contracts and it's parents recursive contracts
    current = loaded
    while not hasattr(current, "contract"):
        if not isinstance(current, pns.data.Namespace):
            return contracts
        current = current.__

    first_pass = True
    while current is not None:
        contract_mods = {} if not current.contract else current.contract._mod
        for contract_mod_name, contract_mod in contract_mods.items():
            if not (
                (contract_mod_name in matching_mods)
                or (contract_mod._alias & matching_mods)
            ):
                continue

            for func_name, contract_func in contract_mod._func.items():
                contract_type = ContractType.from_func(contract_func)
                if not contract_type:
                    continue

                # After the first pass we only consider recursive contracts
                if not first_pass and not contract_type.recursive:
                    continue

                if func_name not in (
                    # Contracts with no function name beyond their type are universal
                    contract_type.value,
                    f"{contract_type.value}_{name}",
                ):
                    continue

                # Add the sub's contracts to this function's contracts if it meets the appropriate criteria
                contracts[contract_type].append(contract_func)

        # Keep looking up the tree for recursive contracts
        first_pass = False
        current = current.__

    return contracts
