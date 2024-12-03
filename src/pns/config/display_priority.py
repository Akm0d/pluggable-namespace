async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Handle the display priority of positional arguments.
    This ensures that positional arguments appear in the defined order

    I.e.

        config:
          my_app:
            my_opt_1:
              positional: True
              display_priority: 1
            my_opt_2:
              positional: True
              display_priority: 2
    """
    display_priority = opts.pns("display_priority", None)
    return {"display_priority": display_priority}


async def sort(hub, cli_args: list[dict[str, object]]) -> list[dict[str, object]]:
    """
    Sort the CLI arguments by display_priority.
    The negative display_priorities were applied to args with no display priority,
    They will come in the order they were defined
    """
    # Sort arguments by display_priority
    return sorted(
        cli_args,
        key=lambda opt: (
            opt["extra"]["display_priority"] is None,
            opt["extra"]["display_priority"],
        ),
    )
