from ._debug import DEBUG_PNS_GETATTR

if DEBUG_PNS_GETATTR:
    from pns._data import *
else:
    from pns._cdata import *  # type: ignore
