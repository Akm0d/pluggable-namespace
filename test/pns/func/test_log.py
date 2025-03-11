import pytest


@pytest.fixture
async def opts(hub):
    async with hub.pop.file.temp(suffix=".log", delete=False) as f:
        yield dict(
            log_datefmt=r"%H:%M:%S",
            log_fmt_logfile=r"%(asctime)s,%(msecs)03d [%(name)-17s][%(levelname)-8s] %(message)s",
            log_file=f.name,
            log_plugin="test",
        )


async def test_trace(hub, opts):
    message = "message"
    opts["log_level"] = "trace"
    await hub.log.init.setup(**opts)
    await hub.log.trace(message)
    await hub.log.init.close()
    assert message in hub.log.test.LOGS


async def test_debug(hub, opts):
    message = "message"
    opts["log_level"] = "debug"
    await hub.log.init.setup(**opts)
    await hub.log.debug(message)
    await hub.log.init.close()
    assert message in hub.log.test.LOGS


async def test_info(hub, opts):
    message = "message"
    opts["log_level"] = "info"
    await hub.log.init.setup(**opts)
    await hub.log.info(message)
    await hub.log.init.close()
    assert message in hub.log.test.LOGS


async def test_error(hub, opts):
    message = "message"
    opts["log_level"] = "error"
    await hub.log.init.setup(**opts)
    await hub.log.error(message)
    await hub.log.init.close()
    assert message in hub.log.test.LOGS


async def test_warning(hub, opts):
    message = "message"
    opts["log_level"] = "warning"
    await hub.log.init.setup(**opts)
    await hub.log.warning(message)
    await hub.log.init.close()
    assert message in hub.log.test.LOGS


async def test_critical(hub, opts):
    message = "message"
    opts["log_level"] = "critical"
    await hub.log.init.setup(**opts)
    await hub.log.critical(message)
    await hub.log.init.close()
    assert message in hub.log.test.LOGS
