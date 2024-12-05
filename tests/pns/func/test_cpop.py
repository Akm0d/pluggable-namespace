async def test_attr(hub):
    # Set an initial value with setattr
    hub.foo = 1
    # Invoke getattr
    hub.foo
    # Change the value with setattr
    hub.foo = 2
    # The change should be successful
    assert hub.foo == 2
