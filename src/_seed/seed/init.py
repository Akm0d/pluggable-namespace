async def cli(hub):
    for location in hub.template._dir:
        template_dir = location / hub.OPT.seed.src
        if template_dir.exists():
            break
    else:
        await hub.log.error(f"Template directory '{hub.OPT.seed.src}' not found")

    await hub.log.info(f"Copying from {template_dir} to {hub.OPT.seed.dest}")

    data = {}
    for arg in hub.OPT.seed.args:
        k, v = arg.split("=", maxsplit=1)
        data[k] = v

    copier_partial = hub.lib.functools.partial(
        hub.lib.copier.run_copy,
        src_path=str(template_dir),
        dst_path=hub.OPT.seed.dest,
        data=data,
        overwrite=hub.OPT.seed.overwrite,
        pretend=hub.OPT.seed.test,
    )

    # Copier creates its own event loop, so we need to use a ThreadPoolExecutor
    with hub.lib.concurrent.futures.ThreadPoolExecutor() as executor:
        await hub._loop.run_in_executor(executor, copier_partial)
