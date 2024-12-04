async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Specify that a given option belongs to a certain subcommand

    I.e.

        config:
          my_app:
            my_opt:
              subcommands:
              - my_subcommand
            my_global_opt:
              - __global__

        subcommands:
          my_app:
            my_subcommand: {}
    """
    subcommands = opts.pop("subcommands", ())
    return {"subcommands": subcommands}


async def create_parsers(
    hub,
    main_parser,
    cli_args: list[object],
    subparsers: dict[str, object],
):
    """
    Create and add CLI parsers and arguments.

    Args:
        hub: The PNS hub instance.
        main_parser (ArgumentParser): The main parser instance.
        parser_args (tuple): Arguments for the parser.
        cli_args (list): List of CLI arguments.
        subparsers (dict): Dictionary of subparsers.

    Returns:
        dict: The parsed CLI options.
    """

    # Add CLI options to the parser
    groups = {}
    subparser_groups = {subcommand: {} for subcommand in subparsers}
    sorted_arguments = await hub.config.display_priority.sort(cli_args)

    for arg_meta in sorted_arguments:
        cli_name = arg_meta["cli_name"]
        options = arg_meta["options"]
        opts = arg_meta["opts"]
        group_name = arg_meta["group_name"]
        extra_subcommands = arg_meta["extra"].subcommands

        # Handle argument groups for top-level parser
        target_group = await hub.config.group.merge(group_name, {None: groups}, None, main_parser)
        if "__global__" in extra_subcommands or not extra_subcommands:
            target_group.add_argument(cli_name, *options, **opts)

        # Handle argument groups for subparsers
        for subcommand in extra_subcommands:
            if subcommand == "__global__":
                for subcmd, sparser in subparsers.items():
                    subparser_group = await hub.config.group.merge(group_name, subparser_groups, subcmd, sparser)
                    subparser_group.add_argument(cli_name, *options, **opts)
            elif subcommand in subparsers:
                subcmd = subcommand
                sparser = subparsers[subcommand]
                subparser_group = await hub.config.group.merge(group_name, subparser_groups, subcmd, sparser)
                subparser_group.add_argument(cli_name, *options, **opts)

    return main_parser
