async def test_opt(hub):
    # Set up the environment with PYTHONPATH
    env = dict(hub.lib.os.environ, PYTHONPATH=":".join(hub.lib.sys.path))

    # Start the CLI process
    result = hub.lib.subprocess.run(
        [hub.lib.sys.executable, "-m", "hub", "OPT.seed"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check the output
    assert hub.lib.yaml.safe_load(result.stdout)

    # Check the exit status
    assert result.returncode == 0


def get_directory_structure(path):
    structure = []
    for file_path in path.rglob("*"):
        relative_path = file_path.relative_to(path)
        structure.append(str(relative_path))
    return sorted(structure)


async def test_cli(hub):
    # Set up the environment with PYTHONPATH
    env = dict(hub.lib.os.environ, PYTHONPATH=":".join(hub.lib.sys.path))

    # Create a temporary directory
    with hub.lib.tempfile.TemporaryDirectory() as temp_dir:
        template_dir = hub.template["plugin"]._static[0]

        # Prepare the CLI command
        command = [
            hub.lib.sys.executable,
            "-m",
            "hub",
            "seed.cli",
            temp_dir,
            "name=name",
            "desc=desc",
        ]

        # Start the CLI process
        result = hub.lib.subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=env,
        )

        # Check the output
        assert result.stdout

        # Check the exit status
        assert (
            result.returncode == 0
        ), f"CLI exited with non-zero status: {result.returncode}"

        # Validate that the template was copied to the temporary directory
        assert hub.lib.os.path.exists(temp_dir), "Destination directory was not created"

        # Get directory structures using pathlib
        source_path = hub.lib.pathlib.Path(template_dir)
        dest_path = hub.lib.pathlib.Path(temp_dir)

        source_structure = get_directory_structure(source_path)
        dest_structure = get_directory_structure(dest_path)

        # Remove 'copier.yml' from the source structure
        source_structure = [
            path
            for path in source_structure
            if path != "copier.yml" and "__pycache__" not in path
        ]

        # Check that the lengths of the directory structures are the same
        assert len(source_structure) == len(dest_structure), (
            f"Source and destination directory structures differ in length: "
            f"{len(source_structure)} != {len(dest_structure)}"
        )

        # Check for presence of specific files, including hidden ones
        expected_files = [".gitignore", ".pre-commit-config.yaml"]
        for file in expected_files:
            assert any(
                file in s for s in dest_structure
            ), f"{file} was not copied to the destination"
