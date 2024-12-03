import multiprocessing


async def test_serialize_hub(hub):
    hub.lib.pickle.dumps(hub)


async def test_serialize_sub(hub):
    hub.lib.pickle.dumps(hub.pns)


async def test_serialize_lib(hub):
    hub.lib.pickle.dumps(hub.lib)


def child_process(hub):
    # Try to access or modify the hub object in the child process
    hub.VAR.value += 1
    return hub.VAR


async def test_hub_multiprocessing(hub):
    hub.VAR = multiprocessing.Value("i", 1)
    # Create a multiprocessing Process
    process = multiprocessing.Process(target=child_process, args=(hub,))
    process.start()
    process.join()

    # Check the result
    assert (
        hub.VAR.value == 2
    ), "Hub object should have been incremented in the child process"
