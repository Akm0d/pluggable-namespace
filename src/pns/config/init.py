DEFAULT_GLOBAL_CLIS = ("pns", "log")


async def load(
    hub,
    cli: str = None,
    cli_config: dict[str, object] = None,
    config: dict[str, object] = None,
    subcommands: dict[str, object] = None,
    global_clis: list[str] = None,
    parser_args: tuple = None,
    parser_init_kwargs: dict[str, object] = None,
):
    """
    Use the pns-config system to load up a fresh configuration for this project
    from the included conf.py file.

    Args:
        cli (str): The name of the authoritative CLI to parse.
        cli_config (dict): The cli_config section of the plugin's config.yaml
        config (dict): The config section of the plugin's config.yaml
        subcommands (dict): The subcommands section of the plugin's config.yaml
        global_clis (list): The namespaces that should be implicitly added to any cli parser or subparser
        parser_args (tuple): Arguments for the parser.
        parser_init_kwargs (dict): Keyword arguments for initializing the parser or subparsers.

    Returns:
        dict: The parsed CLI options.
    """
    if parser_init_kwargs is None:
        parser_init_kwargs = {}
    if cli_config is None:
        cli_config = hub.cli_config

    # Get the plain config data that will tell us about OS vars and defaults
    if config is None:
        config = hub.config.get("config") or {}

    # Merge config and cli_config
    full_config = hub.lib.pns.data.update(cli_config, config, merge_lists=True)

    # These CLI namespaces will be added on top of any cli
    if global_clis is None:
        global_clis = DEFAULT_GLOBAL_CLIS

    # Initialize the active cli, this is what will go into argparse
    active_cli = {}

    # Logging options and config file are part of the global namespace
    for gn in global_clis:
        active_cli.update(full_config.get(gn, {}).copy())

    if subcommands is None:
        subcommands = hub.subcommands
    else:
        active_subcommands = subcommands
    if cli:
        active_subcommands = subcommands.get(cli, {})

        # Grab the named cli last so that it can override globals
        active_cli.update(full_config.get(cli, {}))
        # Handle options that are sourced from other apps
        await hub.config.source.resolve(cli, active_cli, full_config)

        main_parser = await hub.config.init.parser(cli, **parser_init_kwargs)

        # Process config/cli_config values
        subparsers, arguments = await hub.config.init.parse_cli(
            main_parser,
            active_cli=active_cli,
            subcommands=active_subcommands,
        )

        # Add all the cli options to argparse and call the parser
        main_parser = await hub.config.subcommands.create_parsers(main_parser, arguments, subparsers)

        cli_opts = await hub.config.init.parse(main_parser, parser_args)
    else:
        cli_opts = {}

    # Load the config file parameter in the proper order
    pns_config = full_config.get("pns", {}).get("config") or {}
    config_file = (
        cli_opts.get("config")
        or hub.lib.os.environ.get("PNS_CONFIG", pns_config.get("os"))
        or pns_config.get("default")
    )

    config_data = {}
    if config_file:
        config_file = hub.lib.pathlib.Path(config_file)
        if config_file.exists():
            with config_file.open("r") as fh:
                config_data = hub.lib.yaml.safe_load(fh.read())

    if not isinstance(config_data, dict):
        if not config_data:  # The config is just empty, just let the user know
            hub.lib.warnings.warn(
                f"The configuration file {config_file} "
                "retunred no data or failed to load, no configuration "
                "file data will be used"
            )
        else:  # The config is invalid, warn the user
            hub.lib.warnings.warn(
                f"Configuration file must contain "
                f"key/value pairs, not {type(config_data)}, the supplied "
                f"configuration file {config_file} is not returning valid "
                f"data. No configuration file data will be used"
            )
        config_data = {}

    opt = await hub.config.init.prioritize(
        cli=cli,
        cli_opts=cli_opts,
        config=full_config,
        config_file_data=config_data,
        global_clis=global_clis,
    )

    return opt


async def parse(
    hub,
    main_parser: object,
    parser_args: tuple[dict[str, object]],
) -> dict[str, object]:
    # Actually call the main parser
    parsed_args = main_parser.parse_args(args=parser_args)
    return hub.lib.pns.data.NamespaceDict(parsed_args.__dict__)


async def parser(hub, cli: str, parser: object = None, **kwargs) -> object:
    """
    Create a new ArgumentParser or add a subparser to an existing parser.

    Args:
        cli (str): The name of the CLI being parsed.
        parser (ArgumentParser, optional): An existing ArgumentParser instance.
        **kwargs: Additional keyword arguments for ArgumentParser.

    Returns:
        ArgumentParser: The created or modified ArgumentParser instance.
    """
    if cli and "prog" not in kwargs:
        kwargs["prog"] = cli.title()
    if cli and "description" not in kwargs:
        kwargs["description"] = f"{cli.title().replace('_', ' ')} CLI Parser"
    if "conflict_handler" not in kwargs:
        kwargs["conflict_handler"] = "resolve"
    if parser is None:
        return hub.lib.argparse.ArgumentParser(**kwargs)
    else:
        return parser.add_parser(cli, **kwargs)


async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Parse and process CLI options, handling custom config values.

    Args:
        opts (dict): The options to be parsed.

    Returns:
        dict: The processed options.
    """
    extra = {}
    for parser_mod in sorted(hub.config._loaded):
        if parser_mod == "init":
            continue

        if "parse_opt" not in hub.config[parser_mod]:
            continue

        new_extras = await hub.config[parser_mod].parse_opt(opts)
        extra.update(new_extras)
    return hub.lib.pns.data.NamespaceDict(extra)


async def parse_cli(
    hub,
    main_parser,
    active_cli: dict[str, object],
    subcommands: dict[str, object] = None,
) -> dict[str, object]:
    """
    Create a parser and parse all the CLI options.

    Args:
        main_parser (ArgumentParser): The main parser instance.
        active_cli (dict): The active CLI configuration.
        subcommands (dict): The subcommands configuration.

    Returns:
        tuple: A tuple containing the subparsers dictionary and the list of arguments.
    """
    if subcommands is None:
        subcommands = {}
    # Create the main parser for the CLI
    if subcommands:
        sparser = main_parser.add_subparsers(dest="SUBPARSER")
    subparsers = {}

    for subcommand, opts in subcommands.items():
        subparsers[subcommand] = await hub.config.init.parser(subcommand, sparser, **opts)

    # Collect all arguments and their metadata
    arguments = []

    for name, namespace_opts in active_cli.items():
        opts = namespace_opts.copy()
        opts["__name__"] = name
        # Separate/process our custom config values from those consumed by argparse
        extra = await hub.config.init.parse_opt(opts)
        options = extra.options
        group_name = extra.group
        cli_name = opts.pop("__name__")

        argument_meta = {
            "cli_name": cli_name,
            "options": options,
            "opts": opts,
            "group_name": group_name,
            "extra": extra,
        }

        arguments.append(argument_meta)

    return subparsers, arguments


PLACEHOLDER = object()


async def prioritize(
    hub,
    cli: str,
    cli_opts: dict[str, any],
    config: dict[str, any],
    config_file_data: dict[str, any],
    global_clis: list[str],
    *,
    document_parameters: bool = False,
):
    """
    Prioritize configuration data from various sources.

    The order of priority is:
    1. CLI options (highest priority)
    2. Configuration file data
    3. OS environment variables
    4. Default values (lowest priority)
    5. Rewrite the root_dir option so running apps automatically changes dirs to user preferences

    Args:
        cli (str): The name of the CLI being prioritized.
        cli_opts (dict): The parsed CLI options.
        config (dict): The configuration dictionary.
        config_file_data (dict): The data from the configuration file.
        Document_parameters: If True, hub.OPT will contain docstrings for leaf nodes

    Returns:
       pns.data.ImmutableNamespaceDict: The prioritized configuration options.
    """
    opt = hub.lib.collections.defaultdict(dict)
    root_dir = None
    for namespace, args in config.items():
        # Boolean to determine if the given option is part of the active cli
        is_active_namespace = namespace == cli or namespace in global_clis
        for arg, data in args.items():
            is_active_cli = is_active_namespace
            # This option belongs to a different part of the namespace
            if data.get("source"):
                # If the source is not the current namespace, skip it
                if data["source"] != namespace:
                    continue
                is_active_cli = True
            # Initialize value to None
            value = None

            # 1. Check CLI options first
            if is_active_cli and arg in cli_opts:
                value = cli_opts.get(arg)

            # 2. Check config file data if CLI option is not set
            if value is None:
                value = config_file_data.get(namespace, {}).get(arg, PLACEHOLDER)

            # Skip malformed config
            if not isinstance(data, dict):
                msg = f"Invalid data from config.yaml: {data}"
                raise TypeError(msg)

            # 3. Check OS environment variables if config file data is not set
            if value is PLACEHOLDER and "os" in data:
                value = hub.lib.os.environ.get(data["os"], PLACEHOLDER)

            # 4. Use default value if none of the above are set
            if value is PLACEHOLDER:
                if "default" not in data:
                    msg = f"Option '{namespace}.{arg}' has no value from config, os, or defaults"
                    if is_active_cli:
                        raise ValueError(msg)
                value = data.get("default")
            if arg == "root_dir":
                root_dir = value

            if document_parameters:
                # Wrap the value in a class that gives it a docstring
                value = hub.lib.pns.data.wrap_value(arg, value, data.get("help", ""))

            # Set the value in the OPT dictionary
            opt[namespace][arg] = value

    opt["pns"]["subparser"] = cli_opts.get("SUBPARSER", "")
    opt["pns"]["global_clis"] = global_clis

    return opt
