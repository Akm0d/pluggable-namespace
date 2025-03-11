async def test_run_defaults(hub):
    opt = await hub.config.init.load(cli="test", **hub._dynamic.config, parser_args=())
    hub.OPT = opt
    result = await hub.test.init.cli()
    assert result == {"opt1": 1, "opt2": 2}


async def test_opt(hub):
    OPT = await hub.config.init.load(cli="test", **hub._dynamic.config, parser_args=())
    assert OPT.test == {"opt1": 1, "opt2": 2}
