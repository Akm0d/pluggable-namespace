"""
Recursively display nested data
===============================

Example output::

    some key:
        ----------
        foo:
            ----------
            bar:
                baz
            dictionary:
                ----------
                abc:
                    123
                def:
                    456
            list:
                - Hello
                - World
"""


async def to_str(
    hub, s, encoding="utf-8", errors: str = "strict", *, normalize: bool = False
):
    """
    Given str, bytes, bytearray, or unicode (py2), return str
    """

    def _normalize(st):
        try:
            return hub.lib.unicodedata.normalize("NFC", st) if normalize else st
        except TypeError:
            return st

    if not isinstance(encoding, tuple | list):
        encoding = (encoding,)

    if isinstance(s, str):
        return _normalize(s)

    exc = None
    if isinstance(s, bytes | bytearray):
        for enc in encoding:
            try:
                return _normalize(s.decode(enc, errors))
            except UnicodeDecodeError as err:
                exc = err
                continue
        # The only way we get this far is if a UnicodeDecodeError was
        # raised, otherwise we would have already returned (or raised some
        # other exception).
        raise exc  # pylint: disable=raising-bad-type
    msg = f"expected str, bytes, or bytearray not {type(s)}"
    raise TypeError(msg)


async def to_unicode(
    hub, s, encoding="utf-8", errors: str = "strict", *, normalize: bool = False
):
    def _normalize(st):
        return hub.lib.unicodedata.normalize("NFC", st) if normalize else st

    if not isinstance(encoding, tuple | list):
        encoding = (encoding,)

    if isinstance(s, str):
        return _normalize(s)
    elif isinstance(s, bytes | bytearray):
        return _normalize(await hub.output.nested.to_str(s, encoding, errors))
    msg = f"expected str, bytes, or bytearray not {type(s)}"
    raise TypeError(msg)


async def ustring(hub, indent, color, msg, prefix="", suffix="", endc=None):
    if not endc:
        endc = hub.lib.colorama.Fore.RESET
    indent *= " "
    fmt = "{0}{1}{2}{3}{4}{5}"

    try:
        return fmt.format(indent, color, prefix, msg, endc, suffix)
    except UnicodeDecodeError:
        try:
            return fmt.format(
                indent,
                color,
                prefix,
                await hub.output.nested.to_unicode(msg),
                endc,
                suffix,
            )
        except UnicodeDecodeError:
            # msg contains binary data that can't be decoded
            return str(fmt).format(indent, color, prefix, msg, endc, suffix)


async def recurse(hub, ret, indent, prefix, out):
    """
    Recursively iterate down through data structures to determine output
    """
    if isinstance(ret, bytes):
        try:
            ret = ret.decode()
        except UnicodeDecodeError:
            # ret contains binary data that can't be decoded
            pass
    elif isinstance(ret, tuple) and hasattr(ret, "_asdict"):
        # Turn named tuples into dictionaries for output
        ret = ret._asdict()

    if ret is None or ret is True or ret is False:
        out.append(
            await hub.output.nested.ustring(
                indent, hub.lib.colorama.Fore.LIGHTYELLOW_EX, ret, prefix=prefix
            )
        )
    # Number includes all python numbers types
    #  (float, int, long, complex, ...)
    # use repr() to get the full precision also for older python versions
    # as until about python32 it was limited to 12 digits only by default
    elif isinstance(ret, hub.lib.numbers.Number):
        out.append(
            await hub.output.nested.ustring(
                indent, hub.lib.colorama.Fore.LIGHTYELLOW_EX, repr(ret), prefix=prefix
            )
        )
    elif isinstance(ret, str):
        first_line = True
        for line in ret.splitlines():
            line_prefix = " " * len(prefix) if not first_line else prefix
            if isinstance(line, bytes):
                out.append(
                    await hub.output.nested.ustring(
                        indent,
                        hub.lib.colorama.Fore.YELLOW,
                        "Not string data",
                        prefix=line_prefix,
                    )
                )
                break
            out.append(
                await hub.output.nested.ustring(
                    indent, hub.lib.colorama.Fore.GREEN, line, prefix=line_prefix
                )
            )
            first_line = False
    elif isinstance(ret, list | tuple):
        color = hub.lib.colorama.Fore.GREEN
        for ind in ret:
            if isinstance(ind, list | tuple | hub.lib.collections.abc.Mapping):
                out.append(await hub.output.nested.ustring(indent, color, "|_"))
                prefix = (
                    "" if isinstance(ind, hub.lib.collections.abc.Mapping) else "- "
                )
                await hub.output.nested.recurse(ind, indent + 2, prefix, out)
            else:
                await hub.output.nested.recurse(ind, indent, "- ", out)
    elif isinstance(ret, hub.lib.collections.abc.Mapping):
        if indent:
            color = hub.lib.colorama.Fore.CYAN
            out.append(await hub.output.nested.ustring(indent, color, "----------"))

        keys = ret.keys()
        color = hub.lib.colorama.Fore.CYAN
        for key in keys:
            val = ret[key]
            out.append(
                await hub.output.nested.ustring(
                    indent, color, str(key), suffix=":", prefix=prefix
                )
            )
            await hub.output.nested.recurse(val, indent + 4, "", out)
    return out


async def display(hub, data):
    """
    Display ret data
    """
    with hub.lib.colorama.colorama_text():
        lines = await hub.output.nested.recurse(ret=data, indent=0, prefix="", out=[])
    try:
        return "\n".join(lines)
    except UnicodeDecodeError:
        # output contains binary data that can't be decoded
        return "\n".join(
            [str(x) for x in lines]
        )  # future lint: disable=blacklisted-function
