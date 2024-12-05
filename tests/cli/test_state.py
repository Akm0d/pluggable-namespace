async def test_save_and_load(hub, tmp_path):
    state_file = str(tmp_path / "state.pkl")

    # Set some initial state on the hub
    hub.some_attribute = "test_value"

    # Save the hub state to a file
    await hub.cli.state.save(state_file)

    # Clear the hub of these attributes
    hub._clear()
    hub._attrs.clear()

    # Set the state option to point to the state file
    opts = hub.lib.pns.data.ImmutableNamespaceDict({"cli": {"hub_state": state_file}})

    # Restore the hub state
    restored_file = await hub.cli.state.restore(opts)

    # Verify that the hub's state is restored and the correct file path is returned
    assert str(restored_file) == str(state_file)

    # Verify that the attribute from earlier made it back onto the hub
    assert hub.some_attribute == "test_value"
