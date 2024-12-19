BANNER = """
This console is running in an asyncio event loop with a hub.
It allows you to wait for coroutines using the 'await' syntax.
Try: "await hub.lib.asyncio.sleep(1)"
""".strip()


async def run(hub, **kwargs):
    """
    Run an interactive python console that contains the hub, supporting TCP, Unix domain sockets, or standard I/O.

    Args:
        hub (pns.hub.Hub): The global namespace.
        socket(str): Path to the Unix domain socket or a hostname and port <host:port>
        kwargs (dict): Any locals to add to the console namespace.
    """
    # Prepare the local namespace for execution
    local_namespace = {"hub": hub, **kwargs}
    history_file = hub.lib.pathlib.Path(hub.OPT.cli.history_file).expanduser()

    # Set up hub and locals completion
    completer = await hub.cli.completer.get(**kwargs)

    session = hub.lib.prompt_toolkit.PromptSession(
        history=hub.lib.prompt_toolkit.history.FileHistory(history_file),
        completer=completer,
    )

    await hub.lib.aioconsole.aprint(BANNER)

    # Start the interactive loop
    while True:
        try:
            await hub.cli.console.prompt(local_namespace, session)
        except EOFError:
            # Exit handling...
            break
        except KeyboardInterrupt:
            # Keyboard interrupt handling...
            continue
        except Exception:
            # Capture the current exception info
            exc_type, exc_value, exc_traceback = hub.lib.sys.exc_info()
            # Error handling...
            hub.lib.sys.excepthook(exc_type, exc_value, exc_traceback)
            continue


async def prompt(hub, local_namespace: dict, session):
    user_input = await session.prompt_async(">>> ")
    if user_input.strip():
        previous = {k: v for k, v in local_namespace.items() if k != "hub"}
        # Modify the user input to capture the result
        modified_input = f"__result__ = {user_input}"

        try:
            # Try to execute the modified input
            await hub.lib.aioconsole.aexec(modified_input, local_namespace)

        except SyntaxError:
            # If it's a syntax error, execute the original input
            await hub.lib.aioconsole.aexec(user_input, local_namespace)

        result = local_namespace.pop("__result__", None)
        post = {k: v for k, v in local_namespace.items() if k != "hub"}

        # The locals didn't change, this wasn't a variable assignment
        if previous == post:
            # If an async function was called without being assigned to a variable then await it
            if (
                hub.lib.asyncio.iscoroutine(result)
                and result not in local_namespace.values()
            ):
                result = await result

            # If the result wasn't assigned to a variable then print it out
            if result is not None:
                await hub.lib.aioconsole.aprint(result)
