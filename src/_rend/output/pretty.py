async def display(hub, data):
    """
    Display the given data using python's pprint
    """
    return hub.lib.pprint.pprint.pformat(data)
