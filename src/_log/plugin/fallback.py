__virtualname__ = "basic"


async def setup(
    hub,
    log_fmt_console: str = None,
    log_datefmt: str = None,
    log_fmt_logfile: str = None,
    log_file: str = None,
    **kwargs,
):
    if log_fmt_console and log_datefmt:
        console_formatter = hub.lib.logging.Formatter(
            fmt=log_fmt_console, datefmt=log_datefmt
        )
        console_handler = hub.lib.logging.StreamHandler(stream=hub.lib.sys.stderr)
        console_handler.setFormatter(console_formatter)
        hub.log.HANDLER.append(console_handler)

    if log_fmt_logfile and log_file and log_datefmt:
        file_formatter = hub.lib.logging.Formatter(
            fmt=log_fmt_logfile, datefmt=log_datefmt
        )
        file_handler = hub.lib.logging.FileHandler(filename=log_file)
        file_handler.formatter = file_formatter

        hub.log.HANDLER.append(file_handler)
