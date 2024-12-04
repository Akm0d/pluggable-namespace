PLACEHOLDER = object()


async def parameters(hub, opts: dict) -> tuple[list[str], dict[str, object]]:
    """
    Prepare the remaining command-line arguments for use as function parameters.

    Rules for argument parsing:
    - "--arg1 --arg2" is treated as keys mapped to a "True" value.
    - "--arg1" at the end is treated as a key mapped to a "True" value.
    - "--arg value" followed by a value is treated as a key-value pair.
    - "--arg=value" is split on the "=" and treated as a key-value pair.
    - Lone values are treated as positional arguments.
    - All keys have hyphens stripped and inner hyphens replaced with underscores.
    - All values are attempted to be parsed with json.loads, then by splitting
        on the "," and then just as a raw value.

    Args:
        hub (pop.hub.Hub): The global namespace.
        opts (dict): The args parsed for the pop-cli.

    Returns:
        tuple[list[str], dict[str, object]]: A tuple containing a list of
            positional arguments and a dictionary of keyword arguments.
    """
    args = []
    kwargs = {}
    hold = PLACEHOLDER
    for arg in opts.cli.args:
        if hold is not PLACEHOLDER:
            if arg.startswith("--"):
                # This was a flag
                key, _ = await hub.cli.cli.parse_arg(hold, None)
                kwargs[key] = True
                hold = arg
            else:
                # This is the value of the held kwarg
                key, value = await hub.cli.cli.parse_arg(hold, arg)
                kwargs[key] = value
                hold = PLACEHOLDER
        elif "=" in arg:
            key, value = await hub.cli.cli.parse_arg(*arg.split("=", maxsplit=1))
            kwargs[key] = value
            hold = PLACEHOLDER
        elif arg.startswith("--"):
            hold, _ = await hub.cli.cli.parse_arg(arg, None)
        else:
            args.append(arg)

    if hold is not PLACEHOLDER and hold not in kwargs:
        key, _ = await hub.cli.cli.parse_arg(hold, None)
        kwargs[key] = True

    # Process lists, single values, and json values in kwargs
    for key, value in list(kwargs.items()):
        if isinstance(value, list):
            # If only one value in the list, extract it
            if len(value) == 1:
                kwargs[key] = value[0]
            else:
                # Process each item in the list
                kwargs[key] = [await parse_value(hub, v) for v in value]
        else:
            kwargs[key] = await parse_value(hub, value)

    return args, kwargs


async def parse_arg(hub, key: str, value: str):
    """
    Parse a command-line argument key and value, processing the value as JSON if possible.

    Args:
        hub (pop.hub.Hub): The global namespace.
        key (str): The argument key, with leading hyphens and inner hyphens replaced with underscores.
        value (str): The argument value, to be parsed as JSON or split on commas if applicable.

    Returns:
        tuple[str, object]: A tuple containing the processed key and value.
    """
    key = key.replace("-", "_").lstrip("_")
    if not value:
        return key, value
    try:
        # Attempt to interpret the value as json
        value = hub.lib.json.loads(value)
    except Exception:
        # Fallback to manual parsing
        if "," in value:
            value = value.split(",")

    return key, await hub.cli.cli.parse_value(value)


async def parse_value(hub, value: str) -> object:
    """
    Parse a value as a format string, JSON, a comma-separated list, or a raw string.

    Args:
        hub (pop.hub.Hub): The global namespace.
        value (str): The value to be parsed.

    Returns:
        object: The parsed value.
    """
    if not isinstance(value, str):
        return value
    if any(
        (
            hub.lib.re.match(r'^f".*"$', value),
            hub.lib.re.match(r"^hub[\.\w]+(?:\(.*\))?$", value),
        )
    ):
        value = eval(value, {"hub": hub})
        if hub.lib.asyncio.iscoroutine(value):
            value = await value

        return await hub.cli.cli.parse_value(value)

    try:
        return hub.lib.json.loads(value)
    except hub.lib.json.JSONDecodeError:
        if "," in value:
            return value.split(",")
        return value
