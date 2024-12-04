async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Remove 'os' from the argument kwargs, it will be handled by the config prioritizer

    config:
      my_app:
        my_opt:
          os: MY_ENV_VAR
    """
    return {"os": opts.pop("os", False)}
