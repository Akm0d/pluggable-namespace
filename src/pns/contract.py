from ._debug import DEBUG_PNS_GETATTR

if DEBUG_PNS_GETATTR:
    from pns._contract import *
else:
    from pns._ccontract import * # type: ignore

def load_contract(
    contracts,
    mod: object,
    name: str,
) -> list:
    """
    return a Contract object loaded up
    Dynamically create the correct Contracted type
    :param contracts: Contracts functions to add to the sub
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


def create_contracted(
    hub,
    contracts: list,
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
        return ContractedAsyncGen(hub, contracts, func, ref, name, parent, implicit_hub)
    else:
        return Contracted(hub, contracts, func, ref, name, parent, implicit_hub)
