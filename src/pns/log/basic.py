try:
    import aiofiles  # noqa

    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


async def setup(
    hub,
    log_fmt_console: str = None,
    log_datefmt: str = None,
    log_fmt_logfile: str = None,
    log_file: str = None,
    **kwargs,
):
    if log_fmt_console and log_datefmt:
        console_formatter = hub.lib.aiologger.formatters.base.Formatter(
            fmt=log_fmt_console, datefmt=log_datefmt
        )
        console_handler = hub.lib.aiologger.handlers.streams.AsyncStreamHandler(
            formatter=console_formatter, stream=hub.lib.sys.stderr
        )
        hub.log.HANDLER.append(console_handler)

    if log_fmt_logfile and log_file and log_datefmt and HAS_AIOFILES:
        file_formatter = hub.lib.aiologger.formatters.base.Formatter(
            fmt=log_fmt_logfile, datefmt=log_datefmt
        )
        file_handler = hub.lib.aiologger.handlers.files.AsyncFileHandler(
            filename=log_file
        )
        file_handler.formatter = file_formatter

        hub.log.HANDLER.append(file_handler)
