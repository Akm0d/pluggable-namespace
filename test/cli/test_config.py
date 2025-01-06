async def test_override(hub):
    # Make a mutable copy of the vanilla opts
    opt = hub.OPT.copy()
    # These represent the "original" opts that were passed to "hub" by parsing just the config.yaml s
    opt.update({"namespace1": {"opt": 1}, "namespace2": {"opt": 2}})

    # Patch the cli config to include our namespace
    hub._dynamic.config.cli_config.update(
        {
            "namespace1": {"opt": {}},
            "namespace2": {"opt": {}},
        }
    )
    # This should have no effect on the outcome
    hub._dynamic.config.config.update(
        {
            "namespace1": {"opt": {"default": "overridden"}},
            "namespace2": {"opt": {"default": "overridden"}},
        }
    )

    # Run the override function with no new args to verify that defaults get used
    opt0 = hub.lib.copy.deepcopy(opt)
    opt0.update({"cli": {"args": ["OPT"]}})
    opt0 = hub.lib.pns.data.ImmutableNamespaceDict(opt0)
    await hub.cli.config.override("cli", opt0)
    assert hub.OPT.namespace1.opt == 1
    assert hub.OPT.namespace2.opt == 2

    # Patch the original opt so that cli args are passed on to the secondary parser, use namespace1 as the parser
    opt1 = hub.lib.copy.deepcopy(opt)
    opt1.update({"namespace1": {"opt": "value"}, "cli": {"args": ["--opt=test"]}})
    opt1 = hub.lib.pns.data.ImmutableNamespaceDict(opt1)

    await hub.cli.config.override("namespace1", opt1)
    # This value should change because namespace1 is the authoritative CLI
    assert hub.OPT.namespace1.opt == "test"
    # This should get our value from saved config
    assert hub.OPT.namespace2.opt == 2

    # Patch the original opt so that cli args are passed on to the secondary parser, use namespace2 as the parser
    opt2 = hub.lib.copy.deepcopy(opt)
    opt2.update({"namespace1": {"opt": 1}, "cli": {"args": ["--opt=test"]}})
    opt2 = hub.lib.pns.data.ImmutableNamespaceDict(opt2)

    await hub.cli.config.override("namespace2", opt2)
    # This should get our value from saved config
    assert hub.OPT.namespace1.opt == 1
    # This value should change because namespace2 is the authoritative CLI
    assert hub.OPT.namespace2.opt == "test"
