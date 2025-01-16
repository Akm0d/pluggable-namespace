import inspect

from pns.contract import Contracted, ContractType


async def test_contracted_shortcut(hub):
    async def f(hub):
        pass

    c = Contracted(root=hub, contracts=[], func=f, ref="", name="", parent=None)
    c.contracts[ContractType.PRE] = [
        None
    ]  # add some garbage so we raise if we try to evaluate contracts

    with hub.lib.pytest.raises(TypeError):
        await c()
