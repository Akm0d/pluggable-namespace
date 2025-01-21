"""
data.py: Interface module for dynamic data management in a pluggable namespace system.

This module acts as a bridge to the underlying Cython-implemented data structures and utility functions,
providing a Python-accessible interface to the core namespace management functionalities defined in _data.py.
It conditionally imports from either the Cython-compiled version or a debugging version based on the runtime
configuration, allowing seamless integration and debugging capabilities.

By leveraging the conditional imports, this module ensures that development and production environments can
be managed with appropriate levels of performance and logging, enabling developers to switch between detailed
debug outputs and optimized production code seamlessly.

The functionalities imported include:
    - NamespaceDict: A dictionary with attribute-style access.
    - Namespace: A dynamic container for hierarchical data management and module organization.
    - Utility functions like get_alias and update, which support complex data manipulation and querying.

Use this module to access and manipulate namespaces dynamically within applications that benefit from
a modular and extensible architecture.
"""

from ._debug import DEBUG_PNS_GETATTR

if DEBUG_PNS_GETATTR:
    from pns._data import *
else:
    from pns._cdata import *  # type: ignore
