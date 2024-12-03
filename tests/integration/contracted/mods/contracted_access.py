async def two_hubs(hub1, hub2):
    return


async def hub2_dereferenced_call(hub1, hub2):
    hub1.mods.contracted_access.hub1_called = True
    hub2._.hub2_call()


async def hub2_direct_call(hub1, hub2):
    hub1.mods.contracted_access.hub1_called = True
    hub2_call(hub2)


async def hub2_direct_call_kwargs(hub1, hub2):
    hub1.mods.contracted_access.hub1_called = True
    hub2_call(h=hub2)


async def hub2_call(h):
    h.mods.contracted_access.hub2_called = True
