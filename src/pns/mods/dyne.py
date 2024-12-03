from typing import Any


async def get(hub) -> dict[str, Any]:
    """
    Retrive the dynamic dirs data for this hub, if dynamic dirs have not been
    gathered yet then gather it.
    """
    return hub._dynamic.dyne
