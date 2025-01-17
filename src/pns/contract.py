from ._debug import DEBUG_PNS_GETATTR
from collections import defaultdict
import pns.data
import pns.verify

if DEBUG_PNS_GETATTR:
    from pns._contract import Contracted, ContractType
else:
    from pns._ccontract import Contracted, ContractType


CONTRACTS = "__contracts__"


def walk(loaded: "pns.mod.LoadedMod"):
    """
    Find all contracts relevant to the loaded_mod.
        - Finding 'matching_mods' (init, loaded.__name__, and explicit_contracts)
        - Ascending until we reach a sub that has 'contract'
        - Iterating through contract modules
        - Handling the 'first_pass' vs. 'recursive only' logic
    Yields tuples of (contract_type, contract_func_name, contract_func)
    for further filtering by the caller.
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


def match(loaded: "pns.mod.Loaded", name: str) -> dict[ContractType, list[callable]]:
    """
    Recurse the parents of the loaded_mod and collect the contracts and recursive contracts.
    Match them to the current function name and ref.
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
    Verify that all the sig contracts (SIG or R_SIG) actually correspond
    to real functions in the loaded mod, and that their signatures match.
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
