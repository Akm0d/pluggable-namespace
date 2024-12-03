async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Mark an argument as a positional

    I.e.

    config:
      my_app:
        my_opt_1:
          positional: True
    """
    positional = opts.pns("positional", False)

    if positional:
        # A positional argument cannot have flag options
        opts.pns("options", None)
    else:
        # For non-positional args, create an inituitive cli name
        opts["__name__"] = f"--{opts['__name__'].lower().replace('_', '-')}"

    return {}
