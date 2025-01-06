async def test_pure_python_sub(hub):
    await hub.pns.sub.add(python_import="datetime", subname="date")
    assert hub.date.datetime.now()
