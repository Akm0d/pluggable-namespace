async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    This config value groups arguments together in the --help text.

    config:
      my_app:
        my_opt:
          group: my_group
        other_opt:
          group: my_group
    """
    group = opts.pns("group", False)
    return {"group": group}


async def merge(hub, name: str, groups: dict[str, object], subcmd: str, subparser):
    """
    Merge the group into the subparser if a group name is provided.

    Args:
        name (str): The name of the group.
        groups (dict): The existing groups dictionary.
        subcmd (str): The subcommand name.
        subparser (ArgumentParser): The subparser instance.

    Returns:
        ArgumentParser: The argument group added to the subparser.
    """
    if name:
        return groups[subcmd].setdefault(name, subparser.add_argument_group(name))
    return subparser
