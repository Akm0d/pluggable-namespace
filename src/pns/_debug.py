import os

# Whether to skip all the internal getattrs in the debugger
DEBUG_PNS_GETATTR = os.environ.get("PNS_DEBUG", __debug__)
