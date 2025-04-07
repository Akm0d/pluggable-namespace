DEFAULT_CLI = "cli"


async def run(hub):
    """
    Initialize the "hub" cli.

    .. code-block:: bash

        hub <ref> positional1 positional2 --flag1 --flag2 --key1=value --key2 value \
            --list="a,b,c" --json="{'a': 'b'}" --flag3

    Args:
        hub (pns.hub.Hub): The global namespace
    """
    # Grab OPT for cli, arguments it doesn't use will be passed onward to the next cli
    opt = hub.lib.pns.data.NamespaceDict(hub.OPT.copy())
    ref = opt.cli.ref

    # If the ref was a file, then load it as a module and call its main function
    path = hub.lib.pathlib.Path(ref)
    if path.exists():
        new_dirs = {path.parent.absolute()}
        await hub._load_mod(path.stem, dirs=new_dirs, merge=True, ext=path.suffix)
        hub._dynamic = hub.lib.pns.dir.dynamic(new_dirs)
        main_ref = getattr(hub[path.stem], "__main__", "main")
        ref = f"{path.stem}.{main_ref}"
        opt = await hub.config.init.load(cli=DEFAULT_CLI, **hub._dynamic.config)
        hub.OPT = opt

    await hub.log.debug(f"Using ref: hub.{ref}")

    # If no cli was defined, then use the first part of the ref that exists in the cli_config
    cli = opt.cli.cli
    if cli:
        hard_cli = True
    else:
        hard_cli = False
    if ref.strip(".") and not cli:
        finder = hub
        for part in ref.split("."):
            finder = getattr(finder, part)
            # This is not part of pns controlled by config
            if not isinstance(finder, hub.lib.pns.mod.LoadedMod) and not isinstance(
                finder, hub.lib.pns.hub.Sub
            ):
                break
            if part in hub._dynamic.config.cli_config and part != DEFAULT_CLI:
                cli = part

    call_help = False
    if hard_cli or (
        (opt.cli.cli != cli)
        and (
            opt.cli.cli
            or (
                (
                    cli in hub._dynamic.config.cli_config
                    or cli in hub._dynamic.config.config
                )
                and (cli not in opt.get("pns", {}).get("global_clis", ()))
            )
        )
    ):
        await hub.log.debug(f"Loading cli: {cli}")
        # Reload hub.OPT with the cli arguments not consumed by the initial hub
        await hub.cli.config.override(cli, opt)
        args = []
        kwargs = {}
    else:
        await hub.log.debug("Using defualt cli OPTs")
        # Treat all the extra args as parameters for the named ref
        args, kwargs = await hub.cli.cli.parameters(opt)

        call_help = kwargs.pop("help", False)

        if args:
            await hub.log.debug(f"default CLI Args: {' '.join(args)}")
        if kwargs:
            await hub.log.debug(f"default CLI Kwargs: {' '.join(kwargs.keys())}")

    # Get the named reference from the hub
    finder = hub.lib.pns.ref.find(hub, ref)

    # Get the docstring for the object
    if call_help:
        # Make sure that contracts return the docs for their underlying function
        if isinstance(finder, hub.lib.pns.contract.Contracted):
            finder = finder.func
        ret = help(finder)
    else:
        # Call or retrieve the object at the given ref
        ret = await hub.cli.ref.resolve(finder, *args, **kwargs)

    if opt.cli.interactive:
        # Start an asynchronous interactive console
        await hub.cli.console.run(opt=opt, ref=finder, ret=ret)
    elif ret:
        # output the results of finder to the console
        await hub.cli.ref.output(ret)
