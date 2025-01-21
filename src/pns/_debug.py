"""
Debug configuration for conditional performance optimization in a pluggable namespace system.

This module sets up conditional debugging configurations that affect how namespace operations are handled during
development and debugging. By leveraging an environment-based toggle, this module enables or disables stepping
into low-level getattr calls and other namespace internals, facilitating a cleaner and more focused debugging
experience.

Attributes:
    - DEBUG_PNS_GETATTR: A boolean flag that is controlled by the 'PNS_DEBUG' environment variable or the Python's
        built-in __debug__ condition. When set to True, this flag prompts the application to use Cython-optimized
        versions of certain classes, which streamline debugging by bypassing internal namespace operations. This
        allows developers to focus on higher-level application logic without the overhead of stepping through
        optimized and often repetitive internal code.

This configuration is particularly useful for environments where detailed stepping through namespace internals
is unnecessary or distracting. It helps maintain a high level of performance and reduces cognitive load during
debug sessions by minimizing exposure to complex underlying mechanics.
"""

import os

# Whether to skip all the internal getattrs in the debugger
DEBUG_PNS_GETATTR = os.environ.get("PNS_DEBUG", __debug__)
