async def get(hub, **kwargs):
    """
    Creates a completer for the interactive console that provides completion suggestions for the 'hub' namespace.

    Args:
        hub (pns.hub.Hub): The global namespace.

    Returns:
        HubCompleter: A completer object for the interactive console.
    """
    _get_completions = await hub.cli.completer.compute()

    class HashableDocument(hub.lib.prompt_toolkit.document.Document):
        def __init__(self, document):
            self._text = document._text
            self._cursor_position = document._cursor_position
            self._selection = document._selection
            self._cache = document._cache

        def __hash__(self):
            return hash(
                (self._text, self._cursor_position, self._selection, self._cache)
            )

    class HubCompleter(hub.lib.prompt_toolkit.completion.Completer):
        def get_completions(self, document, complete_event):
            return _get_completions(HashableDocument(document))

    completer = HubCompleter()
    # Create a completer for local variables
    local_completer = hub.lib.prompt_toolkit.completion.WordCompleter(
        list(kwargs.keys()), ignore_case=True
    )

    # Create a completer for built-in functions
    builtins = [*list(dir(hub.lib.builtins)), "await", "hub"]
    builtins_completer = hub.lib.prompt_toolkit.completion.WordCompleter(
        builtins, ignore_case=True
    )

    # Combine the hub, local, and built-in completers
    combined_completer = hub.lib.prompt_toolkit.completion.merge_completers(
        [completer, local_completer, builtins_completer]
    )
    return combined_completer


async def compute(hub):
    """
    Return a synchronous function that computes completions for the 'hub' namespace.
    """

    @hub.lib.functools.lru_cache
    def _compute(document):
        # Get the text before the cursor
        text = document.text_before_cursor
        # Find the start index of the "hub." reference
        hub_ref_start = text.find("hub.")

        # Check if "hub." is present in the text
        if hub_ref_start != -1:
            # Remove "hub." prefix and split the reference into parts
            ref = text[hub_ref_start + 4 :]
            parts = ref.split(".")

            # Start with the hub as the root of the reference
            finder = _find(hub, parts[:-1])

            # Get the prefix of the current attribute being completed
            current_attr_prefix = parts[-1]
            attrs = []
            try:
                # Get all attributes and methods of the current object in the hub namespace
                attrs += list(finder)
            except Exception:
                ...

            try:
                attrs += [attr for attr in dir(finder) if attr not in attrs]
            except Exception:
                ...

            # Yield completions that match the current attribute prefix
            for name in attrs:
                try:
                    if name.startswith(current_attr_prefix):
                        display = f"hub.{'.'.join(parts[:-1] + [name])}"
                        yield hub.lib.prompt_toolkit.completion.Completion(
                            name,
                            start_position=-len(current_attr_prefix),
                            display=display,
                        )
                except Exception:
                    continue

            # Do function call completions
            if "(" in text:
                func_name = current_attr_prefix.split("(", maxsplit=1)[0]
                try:
                    func = _find(finder, [func_name])
                    if isinstance(func, hub.lib.pns.contract.Contracted):
                        signature = func.signature
                    elif callable(func):
                        signature = hub.lib.inspect.signature(func)
                    else:
                        return
                    for param in signature.parameters.values():
                        yield hub.lib.prompt_toolkit.completion.Completion(
                            param.name + "=", start_position=0
                        )

                except Exception:
                    ...

    return _compute


def _find(finder: object, parts: list[str]) -> object:
    # Iterate over parts except the last one to traverse the hub namespace
    for p in parts:
        if not p:
            continue
        try:
            finder = getattr(finder, p)
        except AttributeError:
            try:
                finder = finder.__getitem__(p)
            except TypeError:
                if p.isdigit() and hasattr(finder, "__iter__"):
                    try:
                        finder = tuple(finder).__getitem__(int(p))
                    except Exception:
                        # No completions if the path is invalid
                        return
                else:
                    # No completions if the path is invalid
                    return
            except Exception:
                return
        except Exception:
            # No completions if the path is invalid
            return
    return finder
