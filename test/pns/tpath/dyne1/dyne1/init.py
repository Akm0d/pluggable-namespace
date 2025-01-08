async def __init__(hub):
    hub.dyne1.INIT = True
    await hub.pop.sub.add(dyne_name="dyne2")
    await hub.pop.sub.add(dyne_name="dyne3")
