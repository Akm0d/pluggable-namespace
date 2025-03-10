import asyncio
import logging
import functools


async def __init__(hub):
    hub.log.LOGGER = None
    hub.log.HANDLER = None
    hub.log.FORMATTER = None
    hub.log.INT_LEVEL = hub.lib.logging.INFO
    hub.log.QUEUE = hub.lib.asyncio.Queue()

    # Set up aliases for each log function
    hub.log.trace = hub.log.init.trace
    hub.log.info = hub.log.init.info
    hub.log.debug = hub.log.init.debug
    hub.log.error = hub.log.init.error
    hub.log.warning = hub.log.init.warning
    hub.log.warn = hub.log.init.warning
    hub.log.critical = hub.log.init.critical
    hub.log.fatal = hub.log.init.critical


def __func_alias__(hub):
    return {
        name: functools.partial(log, hub, name)
        for name in ("trace", "debug", "info", "warning", "error", "critical")
    }


def log(hub, level: str, *args, **kwargs):
    """
    Log a message with the given name and arguments.
    """
    if not hub.log.LOGGER:
        return hub.lib.asyncio.sleep(0)
    int_level = hub.lib.logging.getLevelName(level.upper())
    hub.log.LOGGER.log(int_level, *args, extra={"hub": hub}, **kwargs)
    # This makes the logging functions awaitable but it isn't necessary
    return hub.lib.asyncio.sleep(0)


async def setup(
    hub,
    log_plugin: str = "init",
    *,
    log_level: str,
    log_fmt_console: str = None,
    log_datefmt: str = None,
    **kwargs,
):
    """
    Initialize the logger with the named plugin
    """
    # Set up trace logger
    hub.lib.logging.addLevelName(5, "TRACE")
    log_level = log_level.split(" ")[-1].upper()

    # Convert log level to integer
    if str(log_level).isdigit():
        hub.log.INT_LEVEL = int(log_level)
    else:
        hub.log.INT_LEVEL = hub.lib.logging.getLevelName(log_level)

    hub.log.FORMATTER = logging.Formatter(fmt=log_fmt_console, datefmt=log_datefmt)
    hub.log.HANDLER = QueueHandler(hub.log.QUEUE)
    hub.log.HANDLER.setFormatter(hub.log.FORMATTER)
    hub.log.LOGGER = logging.getLogger()
    hub.log.LOGGER.setLevel(hub.log.INT_LEVEL)
    hub.log.LOGGER.addHandler(hub.log.HANDLER)


class QueueHandler(logging.Handler):
    """A custom logging handler that puts log messages into a shared queue."""

    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        """Put log record into the queue."""
        if hasattr(record, "hub"):
            hub = record.hub
            ref = hub._last_ref or "hub"
            record.name = ref
        self.queue.put_nowait(record)
