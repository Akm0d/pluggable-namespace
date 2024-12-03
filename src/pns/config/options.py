async def parse_opt(hub, opts: dict[str, object]) -> dict[str, object]:
    """
    Alternate flags that can be used for this config option

    config:
      my_app:
        my_opt:
          options:
          - -o
          - --opt
          - --opt1
    """
    options = opts.pns("options", ())
    return {"options": options}
