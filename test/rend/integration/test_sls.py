async def test_render_sls(hub):
    """
    Verify that SLS files on the hub under hub.sls are rendered and have access to helper functions
    """
    assert "sls" in hub._subs
    ret = await hub.rend.init.parse_subs(["sls"], pipe="jinja|yaml")
    assert ret == {"state_name": {"test.nop": [{"name": "taco"}]}}
