async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Evaluate the "type" string to be a constructor for the actual type
    I.e.

        config:
          my_app:
            my_opt:
              type: str
    """
    type_ = opts.pop("type", None)
    if type_:
        opts["type"] = eval(type_)

    return {}
