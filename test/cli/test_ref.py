# Test find
async def test_find(hub):
    # Set up a nested attribute on the hub for testing
    hub.nested = hub.lib.pns.data.NamespaceDict({"level1": {"level2": "value"}})

    # Test finding a nested attribute
    result = hub.lib.pns.ref.find(hub, "nested.level1.level2")
    assert result == "value"

    # Test finding a non-existent attribute
    with hub.lib.pytest.raises(KeyError):
        hub.lib.pns.ref.find(hub, "nonexistent.attribute")


# Test resolve
async def test_resolve_function(hub):
    # Set up a function on the hub for testing
    async def test_func():
        return "result"

    hub.test_func = test_func

    # Test resolving a function
    result = await hub.cli.ref.resolve(hub.test_func)
    assert result == "result"


async def test_resolve_async_generator(hub):
    # Set up an async generator on the hub for testing
    async def test_gen():
        yield "result1"
        yield "result2"

    hub.test_gen = test_gen

    # Test resolving an async generator
    result = await hub.cli.ref.resolve(hub.test_gen)
    assert result == ["result1", "result2"]


# Test output
async def test_output(hub, capsys):
    # Test output with different types of objects
    await hub.cli.ref.output("string")
    captured = capsys.readouterr()
    assert captured.out == "string\n"

    await hub.cli.ref.output({"key": "value"})
    captured = capsys.readouterr()
    assert "key" in captured.out and "value" in captured.out
