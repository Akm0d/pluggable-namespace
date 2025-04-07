async def test_run_defaults(hub):
    opt = await hub.config.init.load(cli="test", **hub._dynamic.config, parser_args=())
    hub.OPT = opt
    result = await hub.test.init.cli()
    assert result == {"opt1": 1, "opt2": 2}


async def test_opt(hub):
    OPT = await hub.config.init.load(cli="test", **hub._dynamic.config, parser_args=())
    assert OPT.test == {"opt1": 1, "opt2": 2}


async def test_scratch(hub):
    """
    Verify that a one-off python file can be added to the hub and referenced correctly.
    """
    scratch = hub.lib.pathlib.Path(__file__).parent / "scratch"
    ret = await hub.sh[hub.lib.sys.executable](
        "-m", "hub", "-f", f"{scratch}/test.py", "test.main"
    )
    assert "foo" in ret


async def test_scratch_mult(hub):
    """
    Verify that multiple one-off python files can be added to the hub and referenced correctly.
    """
    scratch = hub.lib.pathlib.Path(__file__).parent / "scratch"
    ret = await hub.sh[hub.lib.sys.executable](
        "-m", "hub", "-f", f"{scratch}/test.py", "-f", f"{scratch}/foo.py", "test.main"
    )
    assert "foo" in ret
