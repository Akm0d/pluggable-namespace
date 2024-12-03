async def __init__(hub):
    hub.dyne1.INIT = True
    await hub.pns.sub.add(dyne_name="dyne2")
    await hub.pns.sub.add(dyne_name="dyne3")
