# Test parameters
async def test_parameters_single_flag(hub):
    opts = hub.lib.pns.data.NamespaceDict({"cli": dict(args=["--arg1"])})
    args, kwargs = await hub.cli.cli.parameters(opts)
    assert args == []
    assert kwargs == {"arg1": True}


async def test_parameters_key_value_pair(hub):
    opts = hub.lib.pns.data.NamespaceDict({"cli": {"args": ["--key=value"]}})
    args, kwargs = await hub.cli.cli.parameters(opts)
    assert args == []
    assert kwargs == {"key": "value"}


async def test_parameters_key_value_with_space(hub):
    opts = hub.lib.pns.data.NamespaceDict(
        {"cli": {"args": ["--key", "value"]}}
    )
    args, kwargs = await hub.cli.cli.parameters(opts)
    assert args == []
    assert kwargs == {"key": "value"}


async def test_parameters_multiple_flags(hub):
    opts = hub.lib.pns.data.NamespaceDict(
        {"cli": {"args": ["--arg1", "--arg2"]}}
    )
    args, kwargs = await hub.cli.cli.parameters(opts)
    assert args == []
    assert kwargs == {"arg1": True, "arg2": True}


async def test_parameters_mixed_args(hub):
    opts = hub.lib.pns.data.NamespaceDict(
        {"cli": {"args": ["positional1", "--key=value", "positional2", "--flag"]}}
    )
    args, kwargs = await hub.cli.cli.parameters(opts)
    assert args == ["positional1", "positional2"]
    assert kwargs == {"key": "value", "flag": True}


# Test parse-arg
async def test_parse_arg_simple(hub):
    key, value = await hub.cli.cli.parse_arg("--test", "simple")
    assert key == "test"
    assert value == "simple"


async def test_parse_arg_json(hub):
    key, value = await hub.cli.cli.parse_arg("--test", '{"key": "value"}')
    assert key == "test"
    assert value == {"key": "value"}


async def test_parse_arg_list(hub):
    key, value = await hub.cli.cli.parse_arg("--test", "item1,item2")
    assert key == "test"
    assert value == ["item1", "item2"]


async def test_parse_arg_no_value(hub):
    key, value = await hub.cli.cli.parse_arg("--test", None)
    assert key == "test"
    assert value is None


# Test parse-value
async def test_parse_value_format_string(hub):
    value = 'f"{hub.lib.os.name}"'
    result = await hub.cli.cli.parse_value(value)
    assert result == hub.lib.os.name


async def test_parse_value_json(hub):
    value = '{"key": "value"}'
    result = await hub.cli.cli.parse_value(value)
    assert result == {"key": "value"}


async def test_parse_value_list(hub):
    value = "item1,item2"
    result = await hub.cli.cli.parse_value(value)
    assert result == ["item1", "item2"]


async def test_parse_value_raw_string(hub):
    value = "raw_string"
    result = await hub.cli.cli.parse_value(value)
    assert result == "raw_string"


async def test_parse_value_non_string(hub):
    value = 42
    result = await hub.cli.cli.parse_value(value)
    assert result == 42


async def test_parse_value_coroutine(hub):
    value = "hub.test.mod.echo(1, b=2)"
    result = await hub.cli.cli.parse_value(value)
    assert result == ((1,), {"b": 2})


async def test_parse_value_hub_reference(hub):
    value = "hub.lib.os.name"
    result = await hub.cli.cli.parse_value(value)
    assert result == hub.lib.os.name
