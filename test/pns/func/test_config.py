async def test_load_with_config_file(hub, tmp_path):
    # Test loading with a configuration file
    cli = "test_cli"
    cli_config = hub._dynamic.config.cli_config
    cli_config.update({"test_cli": {"option": {}}})
    config = {"test_cli": {"option": {"default": "default"}}}
    config_file = tmp_path / "config.yaml"
    config_file.write_text("test_cli:\n  option: file_value\n")
    OPT = await hub.config.load(
        cli=cli,
        cli_config=cli_config,
        config=config,
        subcommands={},
        global_clis=["pns"],
        parser_args=[f"--config={config_file}"],
    )
    assert OPT[cli]["option"] == "file_value"


async def test_load_with_subcommands(hub):
    # Test loading with subcommands
    cli = "test_cli"
    cli_config = {"test_cli": {"option": {"default": None}}}
    subcommands = {
        "test_cli": {"subcommand": {"description": "Subcommand description"}}
    }
    OPT = await hub.config.load(
        cli=cli,
        cli_config=cli_config,
        subcommands=subcommands,
        global_clis=[],
        parser_args=["subcommand"],
    )
    assert OPT["pns"]["subparser"] == "subcommand"


async def test_prioritize_with_env_vars(hub):
    # Test prioritizing with environment variables
    cli = "test_cli"
    cli_opts = {}
    config = {"test_cli": {"option": {"os": "TEST_OPTION", "default": "default"}}}
    hub.lib.os.environ["TEST_OPTION"] = "env_value"
    OPT = await hub.config.prioritize(
        cli=cli, cli_opts=cli_opts, config=config, config_file_data={}, global_clis=[]
    )
    assert OPT["test_cli"]["option"] == "env_value"


async def test_load_basic(hub):
    # Test loading with minimal arguments
    with hub.lib.unittest.mock.patch("sys.argv", ["pns"]):
        OPT = await hub.config.init.load()
    assert isinstance(OPT, hub.lib.pns.data.ImmutableNamespaceDict)
    assert "pns" in OPT
    assert "subparser" in OPT["pns"]
    assert "global_clis" in OPT["pns"]
    assert "log" in OPT


async def test_load_with_cli(hub):
    # Test loading with a CLI
    cli = "test_cli"
    cli_config = {"test_cli": {"option": {}}}
    config = {"test_cli": {"option": {"default": "default", "os": "TEST_OPTION"}}}

    hub.lib.os.environ.pop("TEST_OPTION", None)
    # Test the default
    OPT = await hub.config.load(
        cli=cli,
        cli_config=cli_config,
        config=config,
        subcommands={},
        global_clis=[],
        parser_args=[],
    )
    assert OPT[cli]["option"] == "default"

    # Test that os vars overrides default
    hub.lib.os.environ["TEST_OPTION"] = "os"
    OPT = await hub.config.load(
        cli=cli,
        cli_config=cli_config,
        config=config,
        subcommands={},
        global_clis=[],
        parser_args=[],
    )
    assert OPT[cli]["option"] == "os"

    # Test that cli supersedes all
    OPT = await hub.config.load(
        cli=cli,
        cli_config=cli_config,
        config=config,
        subcommands={},
        global_clis=[],
        parser_args=["--option=cli"],
    )
    assert OPT[cli]["option"] == "cli"


async def test_parse_cli(hub):
    # Test parsing CLI options
    cli = "test_cli"
    active_cli = {"option": {"subcommands": ["__global__"]}}
    subcommands = {"subcommand": {}}
    parser_args = ("--option", "cli_value", "subcommand", "--option", "sub_cli_value")
    main_parser = await hub.config.parser(cli)
    subparsers, arguments = await hub.config.parse_cli(
        main_parser, active_cli=active_cli, subcommands=subcommands
    )
    cli_parser = await hub.config.subcommands.create_parsers(
        main_parser, cli_args=arguments, subparsers=subparsers
    )
    cli_opts = await hub.config.init.parse(cli_parser, parser_args)
    assert cli_opts["option"] == "sub_cli_value"
    assert cli_opts["SUBPARSER"] == "subcommand"


async def test_prioritize(hub):
    # Test prioritizing configuration options
    cli = "test_cli"
    cli_opts = {"option": "cli_value"}
    config = {"test_cli": {"option": {"default": "config_value"}}}
    config_file_data = {"test_cli": {"option": "file_value"}}
    OPT = await hub.config.prioritize(
        cli=cli,
        cli_opts=cli_opts,
        config=config,
        config_file_data=config_file_data,
        global_clis=["pns", "log"],
    )
    # CLI options have the highest priority
    assert OPT["test_cli"]["option"] == "cli_value"


async def test_display_priority(hub):
    # Test display_priority for CLI options, including positional arguments
    cli = "test_cli"
    active_cli = {
        "high_priority_option": {"display_priority": 1, "positional": True},
        "low_priority_option": {"display_priority": 10, "positional": True},
        "medium_priority_option": {"display_priority": 5, "positional": True},
        "no_priority_option": {"positional": True},
    }
    parser_args = (
        "high_value",  # High priority positional argument
        "medium_value",  # Medium priority positional argument
        "low_value",  # Low priority positional argument
        "no_priority_value",  # No priority positional argument
    )

    main_parser = await hub.config.parser(cli)
    subparsers, arguments = await hub.config.parse_cli(
        main_parser, active_cli=active_cli
    )
    cli_parser = await hub.config.subcommands.create_parsers(
        main_parser, cli_args=arguments, subparsers=subparsers
    )

    cli_opts = await hub.config.init.parse(cli_parser, parser_args)

    # Verify that the options are parsed correctly
    assert cli_opts["high_priority_option"] == "high_value"
    assert cli_opts["medium_priority_option"] == "medium_value"
    assert cli_opts["low_priority_option"] == "low_value"
    assert cli_opts["no_priority_option"] == "no_priority_value"


async def test_source(hub):
    main_cli = "test_cli"
    source_cli = "source_cli"
    config = {
        main_cli: {"option": {"source": source_cli, "default": "override"}},
        source_cli: {"option": {"default": "value", "choices": ["--opt"]}},
    }

    OPT = await hub.config.load(
        cli=main_cli,
        cli_config=config,
        subcommands={},
        global_clis=[],
        parser_args=[],
    )

    # The option should not exist under the namespace of the main cli
    assert "option" not in OPT[main_cli].keys()
    # Ensure that the option exists under the namespace of the source app
    assert OPT[source_cli]["option"] == "override"
