async def cli(hub):
    template_dir = hub.template[hub.OPT.seed.src]._static[0]
    await hub.log.info(f"Copying from {template_dir} to {hub.OPT.seed.dest}")

    data = {}
    for arg in hub.OPT.seed.args:
        k, v = arg.split("=", maxsplit=1)
        data[k] = v

    copier_partial = hub.lib.functools.partial(
        hub.lib.copier.run_copy,
        src_path=template_dir,
        dst_path=hub.OPT.seed.dest,
        data=data,
        overwrite=hub.OPT.seed.overwrite,
        pretend=hub.OPT.seed.test,
    )

    # Copier creates its own event loop, so we need to use a ThreadPoolExecutor
    with hub.lib.concurrent.futures.ThreadPoolExecutor() as executor:
        await hub._loop.run_in_executor(executor, copier_partial)
