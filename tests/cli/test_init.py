async def test_run_defaults(hub):
    # Set up the environment with PYTHONPATH
    env = dict(hub.lib.os.environ, PYTHONPATH=":".join(hub.lib.sys.path))

    # Start the CLI process
    result = hub.lib.subprocess.run(
        [
            hub.lib.sys.executable,
            "-m",
            "hub",
            "--output=raw",
            "--cli",
            "test",
            "test.init.cli",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check the output
    assert result.stdout.strip() == "{'opt1': 1, 'opt2': 2}"

    # Check the exit status
    assert result.returncode == 0


async def test_opt(hub):
    # Set up the environment with PYTHONPATH
    env = dict(hub.lib.os.environ, PYTHONPATH=":".join(hub.lib.sys.path))

    # Start the CLI process
    result = hub.lib.subprocess.run(
        [hub.lib.sys.executable, "-m", "hub", "--output=raw", "OPT.test"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check the output
    assert result.stdout.strip() == "{'opt1': 1, 'opt2': 2}"

    # Check the exit status
    assert result.returncode == 0
