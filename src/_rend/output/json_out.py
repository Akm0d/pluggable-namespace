"""
Display data in JSON format
"""

__virtualname__ = "json"


async def display(hub, data):
    """
    Print the output data in JSON
    """
    try:
        indent = 4
        return hub.lib.json.dumps(data, default=repr, indent=indent)

    except UnicodeDecodeError as exc:
        return hub.lib.json.dumps(
            {"error": "Unable to serialize output to json", "message": str(exc)}
        )
