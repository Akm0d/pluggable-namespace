import pytest


@pytest.fixture(autouse=True)
async def watch(hub):
    watch = hub.lib.asyncio.create_task(hub.cli.watch.start())
    await hub.lib.asyncio.sleep(0.1)
    yield
    watch.cancel()
    try:
        await watch
    except hub.lib.asyncio.CancelledError:
        ...


async def test_new_module(hub, temp_mod_dir):
    """
    Create a new module and verify that it gets added to the hub
    """
    assert "mod" not in hub.plugin._loaded

    module_path = temp_mod_dir / "mod.py"
    module_path.write_text("a = 1")
    await hub.lib.asyncio.sleep(0.5)

    assert "mod" in hub.plugin._loaded
    assert hub.plugin.mod.a == 1


async def test_del_module(hub, temp_mod_dir):
    """
    Create a module, then delete it and verify that it gets removed from the hub.
    """
    # Setup - create a module
    module_path = temp_mod_dir / "del_mod.py"
    module_path.write_text("a = 1")
    await hub.lib.asyncio.sleep(0.5)  # Allow time for the module to be loaded

    # Verify creation
    assert "del_mod" in hub.plugin._loaded

    # Delete the module
    module_path.unlink()
    await hub.lib.asyncio.sleep(0.5)  # Allow time for the module to be unloaded

    # Verify deletion
    assert "del_mod" not in hub.plugin._loaded


async def test_mod_add_module(hub, temp_mod_dir):
    """
    Modify an existing module and verify that changes are reflected on the hub.
    """
    # Setup - create a module
    module_path = temp_mod_dir / "mod_mod.py"
    module_path.write_text("a = 1")
    await hub.lib.asyncio.sleep(0.5)  # Allow time for the module to be loaded

    # Verify creation
    assert "mod_mod" in hub.plugin._loaded
    assert hub.plugin.mod_mod.a == 1

    # Modify the module
    module_path.write_text("a = 1\nb = 2")
    await hub.lib.asyncio.sleep(0.5)  # Allow time for the module to be reloaded

    # Verify modification
    assert hub.plugin.mod_mod.b == 2


async def test_mod_del_module(hub, temp_mod_dir):
    """
    Modify an existing module by removing content and verify that changes are reflected on the hub.
    """
    # Setup - create a module
    module_path = temp_mod_dir / "mod_del.py"
    module_path.write_text("a = 1\nb = 2")
    await hub.lib.asyncio.sleep(0.5)  # Allow time for the module to be loaded

    # Verify creation
    assert "mod_del" in hub.plugin._loaded
    assert hub.plugin.mod_del.b == 2

    # Modify the module by removing a variable
    module_path.write_text("a = 1")
    await hub.lib.asyncio.sleep(0.5)  # Allow time for the module to be reloaded

    # Verify modification
    assert not hasattr(hub.plugin.mod_del, "b")


async def test_recursive_sub(hub, temp_mod_dir):
    """
    Test creating a new directory with a file inside it, and ensure it is loaded.
    Then delete the directory and ensure it is unloaded from the hub.
    """
    # Create a new directory in the temp_mod_dir
    new_dir = temp_mod_dir / "new_subdir"
    new_dir.mkdir()

    # Create a new module file inside the new directory
    module_path = new_dir / "sub_module.py"
    module_path.write_text("d = 100")

    # Optionally, simulate a delay or trigger to ensure the system processes the new directory
    await hub.lib.asyncio.sleep(1)

    # Check if the new directory with its module is recognized as a sub
    assert (
        "new_subdir" in hub.plugin._subs
    )  # Ensure your system logic matches these attribute names
    assert hub.plugin.new_subdir.sub_module.d == 100

    # Now, delete the directory
    hub.lib.shutil.rmtree(new_dir)

    # Again, simulate a delay or trigger to ensure the system processes the deletion
    await hub.lib.asyncio.sleep(1)

    # Verify the directory and its contents are removed from the hub
    assert "new_subdir" not in hub.plugin._subs


async def test_nested_recursive_sub(hub, temp_mod_dir):
    """
    Test creating a nested directory structure with files at various levels and ensure they are loaded.
    Then delete directories and ensure they are unloaded from the hub.
    """
    # Create nested directories
    nested_dir_level_1 = temp_mod_dir / "level_1"
    nested_dir_level_2 = nested_dir_level_1 / "level_2"
    nested_dir_level_2.mkdir(parents=True)  # Creates all missing parents

    # Create module files at each level
    module_path_l1 = nested_dir_level_1 / "mod_level_1.py"
    module_path_l2 = nested_dir_level_2 / "mod_level_2.py"
    module_path_l1.write_text("x = 1")
    module_path_l2.write_text("y = 2")

    # Simulate a delay to allow the system to process the new directories and files
    await hub.lib.asyncio.sleep(1)

    # Verify that modules are recognized correctly
    assert "level_1" in hub.plugin._subs
    assert "level_2" in hub.plugin.level_1._subs  # Check nested access

    assert hub.plugin.level_1.mod_level_1.x == 1
    assert hub.plugin.level_1.level_2.mod_level_2.y == 2

    # Now, delete the directories
    hub.lib.shutil.rmtree(nested_dir_level_2)

    # Simulate a delay to allow the system to process the deletions
    await hub.lib.asyncio.sleep(1)

    # Verify that directories and their contents are removed from the hub
    assert "level_2" not in hub.plugin.level_1._subs
