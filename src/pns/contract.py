"""
High-level contract management and verification functions for a pluggable namespace system.

This module interfaces with underlying contract management functionalities to dynamically validate and apply
contracts within the namespace architecture. It ensures that components adhere to defined interfaces and
behavioral rules through contracts, enhancing modularity and consistency across system components.

Functions:
    - walk: Traverses loaded modules to identify and yield relevant contracts.
    - match: Collects and organizes contracts applicable to specific functions or modules.
    - verify_sig: Validates that function implementations conform to their specified contracts, particularly in terms of signatures.

The contract enforcement mechanisms facilitated by this module are integral to maintaining a robust, secure,
and compliant system architecture, ensuring that all components operate within predefined boundaries and conditions.
"""

from ._debug import DEBUG_PNS_GETATTR
from collections import defaultdict
from collections.abc import Generator
import pns.data
import pns.verify

if DEBUG_PNS_GETATTR:
    from pns._contract import Contracted, ContractType
else:
    from pns._ccontract import Contracted, ContractType


CONTRACTS = "__contracts__"


def walk(
    loaded: "pns.mod.LoadedMod",
) -> Generator[tuple[ContractType, str, Contracted]]:
    """
    Traverses the hierarchy of namespaces to find and yield contracts applicable to the given module.

    Starting from the specified module, this function ascends through the namespace hierarchy until it
    finds a namespace with defined contracts. It then iterates over these contracts, yielding those that
    match the module's name, aliases, or explicit contracts specified in the module.

    Parameters:
        loaded (pns.mod.LoadedMod): The module for which contracts need to be identified.

    Yields:
        tuple: A tuple containing the contract type, the contract function name, and the contract function object.
        These are used for further processing or application to the module.

    Notes:
        - The function employs a 'first_pass' flag to differentiate initial contract gathering from recursive
            checks which only yield contracts marked as recursive.
    """
    explicit_contracts = getattr(loaded, CONTRACTS, ())
    matching_mods = {"init", loaded.__name__, *explicit_contracts}

    # Ascend until we find a sub that has 'contract'
    current = loaded
    while not hasattr(current, "contract"):
        if not isinstance(current, pns.data.Namespace):
            return  # No yield; no contracts
        current = current.__

    first_pass = True
    while current is not None:
        contract_mods = {} if not current.contract else current.contract._mod
        for contract_mod_name, contract_mod in contract_mods.items():
            # Must match the 'matching_mods' or alias
            if not (
                (contract_mod_name in matching_mods)
                or (contract_mod._alias & matching_mods)
            ):
                continue

            # Iterate all functions in that contract module
            for contract_func_name, contract_func in contract_mod._func.items():
                contract_type = ContractType.from_func(contract_func)
                if not contract_type:
                    continue

                # After first pass, only yield 'recursive' contracts
                if not first_pass and not contract_type.recursive:
                    continue

                yield (contract_type, contract_func_name, contract_func)

        first_pass = False
        current = current.__


def match(loaded: "pns.mod.Loaded", name: str) -> dict[ContractType, list[Contracted]]:
    """
    Collects and organizes contracts applicable to a specified function within a loaded module.

    This function calls 'walk' to retrieve relevant contracts and then filters them based on the
    function name, storing matches in a dictionary categorized by contract type.

    Parameters:
        loaded (pns.mod.Loaded): The loaded module containing the function.
        name (str): The name of the function to match contracts against.

    Returns:
        dict: A dictionary mapping contract types to lists of callable contract functions.
    """
    contracts = defaultdict(list)

    for contract_type, contract_func_name, contract_func in walk(loaded):
        # Only proceed if the contract_func_name matches the function name or is universal
        if contract_func_name not in (
            contract_type.value,
            f"{contract_type.value}_{name}",
        ):
            continue
        # If it meets that criterion, store it in the dict
        contracts[contract_type].append(contract_func)

    return contracts


def verify_sig(
    loaded: "pns.mod.LoadedMod",
):
    """
    Verifies that all signature contracts (SIG or R_SIG) correspond to real functions in the loaded module
    and checks if their signatures match.

    This function ensures that each signature-enforcing contract has a corresponding function in the module
    and that the function's signature aligns with the contract's requirements.

    Parameters:
        loaded (pns.mod.LoadedMod): The module whose functions are to be verified against signature contracts.

    Raises:
        SyntaxError: If any discrepancies are found between the contract signatures and the actual function signatures.
    """
    errors = []

    for contract_type, contract_func_name, contract_func in walk(loaded):
        # Only care about Signature types
        if contract_type not in (
            pns.contract.ContractType.SIG,
            pns.contract.ContractType.R_SIG,
        ):
            continue

        # Derive the function name it references by stripping e.g. "sig_" or "r_sig_"
        check_name = contract_func_name[len(f"{contract_type.value}_") :]

        # If that function doesn't exist in loaded._func, add to the errors
        # If check_name is empty, its a universal contract and we still match the signature
        if check_name and check_name not in loaded._func:
            errors.append(
                f"Function '{check_name}' missing from module '{loaded.__ref__}'"
            )
        else:
            # Verify that the signatures match
            errors.extend(pns.verify.sig(loaded._func[check_name], contract_func))

    if errors:
        raise SyntaxError("\n".join(errors))
