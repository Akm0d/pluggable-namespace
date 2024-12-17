import pns.hub
import os

# Default to c versions of contract and data which skip all the internal getattrs in the debugger
DEBUG_PNS_GETATTR = os.environ.get("PNS_DEBUG", False)
if DEBUG_PNS_GETATTR:
    import pns.contract as contract
    import pns.data as data
else:
    import pns.ccontract as contract
    import pns.cdata as data

Contracted = contract.Contracted
ContractedContext = contract.ContractedContext
Hub = pns.hub.Hub
Sub = pns.hub.Sub
LoadedMod = data.LoadedMod
Namespace = data.Namespace
NamespaceDict = data.NamespaceDict
