async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Include an option defined in another app's config in this app's CLI
    Merge over the source app's config for the option.

    It will still show up under the namespace of the other app.

    I.e.

    config:
      my_app:
        my_opt:
          source: other_app
          default: override

      other_app:
        my_opt:
          default: value
    """
    opts.pop("source", None)

    # This is already handled in hub.config.load since it needs to happen before everything else.

    return {}


async def resolve(hub, cli: str, active_cli: dict[str, object], full_config: dict[str, object]):
    """
    Add an option from another app's cli_config to the active cli
    """
    new_stuff = {}
    for name, opt in active_cli.items():
        source = opt.pop("source", None)
        if not source:
            continue
        # Get the config for the opt from the source
        if not full_config.get(source):
            full_config[source] = {}
        if not full_config[source].get(name):
            full_config[source][name] = {}

        # Override the sourced option config with the values from the active cli
        full_config[source][name].update(opt)
        new_stuff[name] = full_config[source][name]
        new_stuff[name]["source"] = source

    for key in new_stuff:
        # Ensure that the key only shows up under the source's namespace
        full_config[cli].pop(key, None)

    active_cli.update(new_stuff)
