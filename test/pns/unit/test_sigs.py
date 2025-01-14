# from pns.verify import sig
def sig(): ...


async def test_sig_default_values():
    def sig_default(hub, name=None):
        pass

    def no_default(hub, name):
        pass

    result = sig(no_default, sig_default)
    assert 'no_default: Parameter "name" must have a default value' in result[0]
    assert "Enforcing signature: " in result[1]

    def default(hub, name=None):
        pass

    result = sig(default, sig_default)
    assert [] == result


async def test_sig_no_default_values():
    def sig_default(hub, name):
        pass

    def no_default(hub, name):
        pass

    result = sig(no_default, sig_default)
    assert [] == result

    def default(hub, name=None):
        pass

    result = sig(default, sig_default)
    assert 'default: Parameter "name" cannot have a default value' in result[0]
    assert "Enforcing signature: " in result[1]


async def test_sig_no_default_after_star():
    def sig_star(hub, name, *, kwarg_only):
        pass

    def kwarg_not_defined(hub, name, *, kwarg_only):
        pass

    result = sig(kwarg_not_defined, sig_star)
    assert result == []


async def test_sig_error_shows_sig_path():
    def sig_test():
        pass

    def test(param):
        pass

    result = sig(test, sig_test)

    assert "Enforcing signature: " in result[1]
    assert result[1].endswith("test_sigs.py::sig_test")
    assert len(result[1]) > 46
