async def __init__(hub):
    hub.log.LOGGER = {}
    hub.log.HANDLER = []
    hub.log.INT_LEVEL = hub.lib.logging.INFO
    hub.log.QUEUE = hub.lib.asyncio.Queue()

    # Set up aliases for each log function
    hub.log.trace = hub._.trace
    hub.log.info = hub._.info
    hub.log.debug = hub._.debug
    hub.log.error = hub._.error
    hub.log.warning = hub._.warning
    hub.log.warn = hub._.warning
    hub.log.critical = hub._.critical
    hub.log.fatal = hub._.critical


async def get_logger(hub, name: str):
    """
    Create a logger for the given ref with all the configured handlers
    """
    if name not in hub.log.LOGGER:
        if hub.log.HANDLER:
            logger = hub.lib.aiologger.Logger(name=name, level=hub.log.INT_LEVEL)
            for handler in hub.log.HANDLER:
                handler.level = hub.log.INT_LEVEL
                logger.add_handler(handler)
        else:
            logger = hub.lib.aiologger.Logger.with_default_handlers(name=name, level=hub.log.INT_LEVEL)
        logger.emit = hub.log.init.emit

        hub.log.LOGGER[name] = logger

    return hub.log.LOGGER[name]


async def setup(hub, log_plugin: str = "init", *, log_level: str, log_file: str, **kwargs):
    """
    Initialize the logger with the named plugin
    """
    if not __debug__:
        return

    if hub.log.HANDLER:
        # We already set up the logger
        return
    # Set up trace logger
    hub.lib.aiologger.levels.LEVEL_TO_NAME[5] = "TRACE"
    hub.lib.logging.addLevelName(5, "TRACE")

    log_level = log_level.split(" ")[-1].upper()

    # Convert log level to integer
    if str(log_level).isdigit():
        hub.log.INT_LEVEL = int(log_level)
    else:
        hub.log.INT_LEVEL = hub.lib.logging.getLevelName(log_level)

    if log_plugin != "init":
        # Create the log file
        if log_file:
            path = hub.lib.pathlib.Path(log_file).expanduser()
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            log_file = str(path)
        await hub.log[log_plugin].setup(log_file=log_file, **kwargs)

    if not __debug__:
        return

    # Create a handler that puts the main python log messages through aiologger via an asynchronous Queue
    class _AsyncHandler(hub.lib.logging.Handler):
        def emit(self, record):
            if hub.lib.asyncio._get_running_loop() is None:
                return
            hub._auto(hub.log.init.emit(record))

    async_handler = _AsyncHandler()

    # Replace all existing synchronous loggers with the aiologger
    for logger in hub.lib.logging.root.manager.loggerDict.values():
        if isinstance(logger, hub.lib.logging.Logger):
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
            logger.addHandler(async_handler)
            logger.setLevel(hub.log.INT_LEVEL)


async def emit(hub, record):
    if not __debug__:
        return
    logger_name = f"lib.{record.name}"
    logger = await hub.log.init.get_logger(logger_name)
    message = record.getMessage()
    # Pass the log record to the appropriate aiologger instance
    await logger._log(
        # Round to the nearest level that is a multiple of 10
        (record.levelno // 10) * 10,
        message,
        (),
        extra={"lineno": record.lineno, "filepath": record.pathname},
    )


def _get_caller_ref(hub) -> str:
    ref = hub._last_call._last_ref or "hub"
    return ref


async def trace(hub, msg: str, *args, **kwargs):
    if not __debug__:
        return
    ref = _get_caller_ref(hub)
    logger = await hub.log.init.get_logger(ref)
    await logger._log(5, msg, args, **kwargs)


async def debug(hub, msg: str, *args, **kwargs):
    if not __debug__:
        return
    ref = _get_caller_ref(hub)
    logger = await hub.log.init.get_logger(ref)
    await logger.debug(msg, *args, **kwargs)


async def info(hub, msg: str, *args, **kwargs):
    if not __debug__:
        return
    ref = _get_caller_ref(hub)
    logger = await hub.log.init.get_logger(ref)
    await logger.info(msg, *args, **kwargs)


async def warning(hub, msg: str, *args, **kwargs):
    if not __debug__:
        return
    ref = _get_caller_ref(hub)
    logger = await hub.log.init.get_logger(ref)
    await logger.warning(msg, *args, **kwargs)


async def error(hub, msg: str, *args, **kwargs):
    if not __debug__:
        return
    ref = _get_caller_ref(hub)
    logger = await hub.log.init.get_logger(ref)
    await logger.error(msg, *args, **kwargs)


async def critical(hub, msg: str, *args, **kwargs):
    if not __debug__:
        return
    ref = _get_caller_ref(hub)
    logger = await hub.log.init.get_logger(ref)
    await logger.critical(msg, *args, **kwargs)
