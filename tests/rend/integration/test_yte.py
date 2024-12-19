async def test_render(hub):
    """
    test rend.yte.render
    """
    hub.foo = "bar"
    ret = await hub.rend.yte.render("a: ?hub.foo")
    assert ret == {"a": "bar"}


async def test_render_async(hub):
    """
    test rend.yte.render with an async call
    """
    # Use jinja to call an async function then render the rest of the line with yte
    with hub.lib.tempfile.NamedTemporaryFile() as tmp:
        template = r'a: "?await hub.test.t.func(a=1) + (hub.OPT.log.log_level,)"'
        tmp.write(template.encode())
        tmp.flush()
        ret = await hub.rend.init.parse(tmp.name, pipe="yte")

    assert ret == {"a": ((), {"a": 1}, "warning")}
