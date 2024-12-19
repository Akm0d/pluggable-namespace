from ._debug import DEBUG_PNS_GETATTR

if DEBUG_PNS_GETATTR:
    from pns._contract import *
else:
    from pns._ccontract import *
