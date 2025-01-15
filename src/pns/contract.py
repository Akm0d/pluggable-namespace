from ._debug import DEBUG_PNS_GETATTR
from collections.abc import Callable
from collections import defaultdict
import pns.data

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


def match(
    loaded: "pns.mod.Loaded", func: Callable
) -> dict[ContractType, list[Callable]]:
    """
    Recurse the parents of the loaded_mod and collect the contracts and recursive contracts.
    Match them to the current function name and ref
    """
    contracts = defaultdict(list)
    name = func.__name__
    explicit_contracts = getattr(loaded, CONTRACTS, ())
    matching_mods = {"init", loaded.__name__, *explicit_contracts}

    # Move up the tree until we are on the nearest Sub
    # We will match with the current sub's contracts and it's parents recursive contracts
    current = loaded
    while not hasattr(current, "contract"):
        if not isinstance(current, pns.data.Namespace):
            return contracts
        current = current.__

    while current is not None:
        for contract_type, sub_contracts in current.contract.items():
            # Add the sub's contracts to this functions contracts if it meets the appropriate criteria
            for sub_contract in sub_contracts:
                # Contracts in an "init" module are universal
                sub_name, mod_ref = sub_contract.__ref__.split(".contract.", maxsplit=1)
                mod_name, contract_func_name = mod_ref.split(".", maxsplit=1)
                if sub_contract.__.__name__ not in matching_mods:
                    continue
                # Contracts with no function name beyond their type are universal
                if sub_contract.__name__ not in (
                    contract_type.value,
                    f"{contract_type.value}_{name}",
                ):
                    continue
                contracts[contract_type].append(sub_contract)
        current = current.__

    return contracts


def recurse(loaded_mod: "pns.mod.LoadedMod") -> dict[ContractType, list[Callable]]:
    """
    Recurse the parents of the loaded_mod and collect the contracts and recursive contracts
    """
    while current is not None:

        # TODO iterate over the parent subs and add their recursive contracts to this one
        for func in current.contract.values():
            contract_type = ContractType.from_func(func)
            if not contract_type:
                continue
            contracts[contract_type].append(func)

        current = current.__

    return contracts
