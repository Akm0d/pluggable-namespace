async def __init__(hub):
    hub.log.test.LOGS = []


async def process(hub, msg: str):
    """
    For testing simply append logs to a list
    """
    hub.log.test.LOGS.append(msg)
