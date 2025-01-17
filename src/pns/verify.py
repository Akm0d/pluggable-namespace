import inspect
from collections.abc import Callable

NO_TYPE_ANNOTATION = object()


def sig_map(ver: Callable) -> dict[str, object]:
    """
    Generates the map dict for the signature verification
    """
    vsig = inspect.signature(ver)
    vparams = list(vsig.parameters.values())
    vdat = {
        "args": [],
        "v_pos": -1,
        "kw": [],
        "kwargs": False,
        "ann": {},
        "defaults": {},
    }
    for ind in range(len(vparams)):
        param = vparams[ind]
        val = param.kind.value
        name = param.name
        if val == inspect._POSITIONAL_ONLY or val == inspect._POSITIONAL_OR_KEYWORD:
            vdat["args"].append(name)
            if param.default != inspect._empty:  # Is a KW, can be inside of **kwargs
                vdat["kw"].append(name)
        elif val == inspect._VAR_POSITIONAL:
            vdat["v_pos"] = ind
        elif val == inspect._KEYWORD_ONLY:
            vdat["kw"].append(name)
        elif val == inspect._VAR_KEYWORD:
            vdat["kwargs"] = ind
        if param.annotation != inspect._empty:
            vdat["ann"][name] = param.annotation
        if param.default != inspect._empty:
            vdat["defaults"][name] = param.default
    return vdat


def sig(func: Callable, sig_func: Callable) -> list[str]:
    """
    Takes 2 functions, the first function is verified to have a parameter signature
    compatible with the second function
    """
    errors = []
    fsig = inspect.signature(func)
    fparams = list(fsig.parameters.values())
    vdat = sig_map(sig_func)
    arg_len = len(vdat["args"])
    v_pos = False
    f_name = getattr(func, "__name__", func.__class__.__name__)
    for ind in range(len(fparams)):
        param = fparams[ind]
        val = param.kind.value
        name = param.name
        has_default = param.default != inspect._empty
        ann = param.annotation

        vann = vdat["ann"].get(name, NO_TYPE_ANNOTATION)
        # Only enforce type if one is given in the signature, it won't be for *args and **kwargs
        if vann is not NO_TYPE_ANNOTATION and vann != ann:
            errors.append(f'{f_name}: Parameter "{name}" is type "{ann}" not "{vann}"')

        # if the signature argument doesn't have a default, but the function does:
        if (
            name in vdat["args"]
            and name not in vdat["defaults"]
            and param.default != inspect._empty
        ):
            errors.append(f'{f_name}: Parameter "{name}" cannot have a default value')
        # if the signature argument *does* have a default, but the function doesn't:
        elif name in vdat["defaults"] and param.default == inspect._empty:
            errors.append(f'{f_name}: Parameter "{name}" must have a default value')

        if val == inspect._POSITIONAL_ONLY or val == inspect._POSITIONAL_OR_KEYWORD:
            if ind >= arg_len:  # Past available positional args
                if not vdat["v_pos"] == -1:  # Has a *args
                    if ind >= vdat["v_pos"] and v_pos:
                        # Invalid unless it is a kw
                        if name not in vdat["kw"]:
                            # Is a kw
                            errors.append(f'Parameter "{name}" is invalid')
                        if vdat["kwargs"] is False:
                            errors.append(
                                f'{f_name}: Parameter "{name}" not defined as kw only'
                            )
                        continue
                elif vdat["kwargs"] is not False and not has_default:
                    errors.append(
                        f'{f_name}: Parameter "{name}" is past available positional params'
                    )
                elif vdat["kwargs"] is False:
                    errors.append(
                        f'{f_name}: Parameter "{name}" is past available positional params'
                    )
            else:
                v_param = vdat["args"][ind]
                if v_param != name:
                    errors.append(
                        f'{f_name}: Parameter "{name}" does not have the correct name: {v_param}'
                    )
        elif val == inspect._VAR_POSITIONAL:
            v_pos = True
            if vdat["v_pos"] == -1:
                errors.append(f"{f_name}: *args are not permitted as a parameter")
            elif ind < vdat["v_pos"]:
                errors.append(
                    f'{f_name}: Parameter "{name}" is not in the correct position for *args'
                )
        elif val == inspect._KEYWORD_ONLY:
            if name not in vdat["kw"] and not vdat["kwargs"]:
                errors.append(
                    f'{f_name}: Parameter "{name}" is not available as a kwarg'
                )
        elif val == inspect._VAR_KEYWORD:
            if vdat["kwargs"] is False:
                errors.append(f"{f_name}: **kwargs are not permitted as a parameter")
    if errors:
        if hasattr(sig_func.__code__, "co_filename"):
            errors.append(
                f"Enforcing signature: {sig_func.__code__.co_filename}::{sig_func.__name__}"
            )
        else:
            errors.append(
                f"Enforcing signature: {sig_func.__module__}.{sig_func.__name__}"
            )
    return errors
