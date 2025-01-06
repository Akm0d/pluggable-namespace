async def setup(hub, **kwargs):
    """
    Given the configuration data set up the logger
    """
    cf = hub.lib.aiologger.formatters.base.Formatter(
        fmt=kwargs["log_fmt_console"], datefmt=kwargs["log_datefmt"]
    )
    ch = hub.lib.aiologger.handlers.streams.AsyncStreamHandler(
        formatter=cf, loop=hub.pns.Loop, stream=hub.lib.sys.stderr
    )
    hub.log.HANDLER.append(ch)

    ff = hub.lib.aiologger.formatters.base.Formatter(
        fmt=kwargs["log_fmt_logfile"], datefmt=kwargs["log_datefmt"]
    )
    fh = hub.lib.aiologger.handlers.files.AsyncTimedRotatingFileHandler(
        kwargs["log_file"]
    )
    fh.formatter = ff
    hub.log.HANDLER.append(fh)
