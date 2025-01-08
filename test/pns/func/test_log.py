import tempfile

import pytest


@pytest.fixture
def opts():
    with tempfile.NamedTemporaryFile(suffix=".log") as f:
        yield dict(
            log_datefmt=r"%H:%M:%S",
            log_fmt_logfile=r"%(asctime)s,%(msecs)03d [%(name)-17s][%(levelname)-8s] %(message)s",
            log_file=f.name,
            log_plugin="basic",
        )


async def test_trace(hub, opts):
    message = "message"
    opts["log_level"] = "trace"
    await hub.pop.sub.add(dyne_name="log")
    await hub.log.init.setup(**opts)
    await hub.log.trace(message)
    with open(opts["log_file"]) as fh:
        contents = fh.read()
        assert message in contents


async def test_debug(hub, opts):
    message = "message"
    opts["log_level"] = "debug"
    await hub.pop.sub.add(dyne_name="log")
    await hub.log.init.setup(**opts)
    await hub.log.debug(message)
    with open(opts["log_file"]) as fh:
        contents = fh.read()
        assert message in contents


async def test_info(hub, opts):
    message = "message"
    opts["log_level"] = "info"
    await hub.pop.sub.add(dyne_name="log")
    await hub.log.init.setup(**opts)
    await hub.log.info(message)
    with open(opts["log_file"]) as fh:
        contents = fh.read()
        assert message in contents


async def test_error(hub, opts):
    message = "message"
    opts["log_level"] = "error"
    await hub.pop.sub.add(dyne_name="log")
    await hub.log.init.setup(**opts)
    await hub.log.error(message)
    with open(opts["log_file"]) as fh:
        contents = fh.read()
        assert message in contents


async def test_warning(hub, opts):
    message = "message"
    opts["log_level"] = "warning"
    await hub.pop.sub.add(dyne_name="log")
    await hub.log.init.setup(**opts)
    await hub.log.warning(message)
    with open(opts["log_file"]) as fh:
        contents = fh.read()
        assert message in contents


async def test_critical(hub, opts):
    message = "message"
    opts["log_level"] = "critical"
    await hub.pop.sub.add(dyne_name="log")
    await hub.log.init.setup(**opts)
    await hub.log.critical(message)
    with open(opts["log_file"]) as fh:
        contents = fh.read()
        assert message in contents
