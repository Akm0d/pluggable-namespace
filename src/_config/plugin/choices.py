async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Handle choices that may come from a loaded mod.

    You specify a sub on the hub for "choices" to dynamically use the loaded mods of that sub as the choices

    I.e.

    config:
      my_app:
        my_opt:
          choices:
            my_sub

    Otherwise, you can specify a list of static choices that may be used

    I.e.

    config:
      my_app:
        my_opt:
          choices:
            - choice_1
            - choice_2
    """
    choices = opts.pop("choices", ())
    if isinstance(choices, str):
        finder = hub
        for part in choices.split("."):
            try:
                finder = getattr(finder, part)
            except AttributeError:
                return {}

        opts["choices"] = sorted(finder)

    return {}
