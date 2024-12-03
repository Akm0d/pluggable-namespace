import inspect

from cpns.contract import Contracted


async def test_contracted_shortcut(hub):
    async def f(hub):
        pass

    c = Contracted(hub=hub, contracts=[], func=f, ref="", name="", parent=None)
    c.contract_functions["pre"] = [
        None
    ]  # add some garbage so we raise if we try to evaluate contracts

    await c()


async def test_contracted_inspect():
    def f(hub, p1, p2=None):
        pass

    c = Contracted(None, [], f, "", "", None)

    assert str(inspect.signature(c)) == str(inspect.signature(f))
    assert str(inspect.signature(c)) == "(hub, p1, p2=None)"
