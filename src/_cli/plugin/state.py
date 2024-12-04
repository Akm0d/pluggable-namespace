async def restore(hub, opts: dict) -> str:
    # Try to get a saved hub
    try:
        if opts.cli.hub_state:
            hub_state = await hub.cli.cli.parse_value(opts.cli.hub_state)

            # Load the saved state of the hub from a file in memory
            hub_state_file = hub.lib.pathlib.Path(hub_state).expanduser()
            await hub.log.debug(f"Restoring hub from {hub_state_file}")
            await hub.cli.state.load(hub_state_file)
            return hub_state_file
    except Exception as e:
        await hub.log.error(f"Could not restore hub from '{hub_state_file}': {e}")


async def load(hub, state_file):
    """_summary_
    Read a hub state from a pickle file and add its attributes to the current hub.

    Args:
        hub (pop.hub.Hub): The global namespace
        state_file (str): A pickle file that contains serialized hub data
        cli (str): The cli config to load on the new hub
    """
    state_file = hub.lib.pathlib.Path(state_file)
    if state_file.exists():
        try:
            with state_file.open("rb") as f:
                contents = f.read()
                state = hub.lib.pickle.loads(contents)
        except Exception as e:
            await hub.log.error(f"Error loading hub state: {e}")
            return

        if not state:
            return

        hub.__setstate__(state)


async def save(hub, state_file):
    """_summary_
    Serialize the hub and write it to a file.

    Args:
        hub (pop.hub.Hub): The global namespace
        state_file (str): A pickle file to writ ethe serialized hub to.
    """
    state_file = hub.lib.pathlib.Path(state_file)
    state_file = hub.lib.pathlib.Path(state_file)
    # Manually retrieve the state using __getstate__
    state = hub.__getstate__()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("wb") as f:
        f.write(hub.lib.pickle.dumps(state))
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("wb") as f:
        f.write(hub.lib.pickle.dumps(state))
