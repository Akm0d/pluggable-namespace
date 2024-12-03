"""
Pns related exceptions
"""


class PnsBaseException(Exception):  # noqa
    """
    Base exception where all of Pns's exceptions derive
    """


class PnsError(PnsBaseException):
    """
    General purpose pns.exception to signal an error
    """


class PnsLoadError(PnsBaseException):
    """
    Exception raised when a pns module fails to load
    """


class PnsLookupError(PnsBaseException):
    """
    Exception raised when a pns module lookup fails
    """


class ContractModuleException(PnsBaseException):
    """
    Exception raised when a function specified in a contract as required
    to exist is not found in the loaded module
    """


class ContractFuncException(PnsBaseException):
    """
    Exception raised when a function specified in a contract as required
    to exist is found on the module but it's not function
    """


class ContractSigException(PnsBaseException):
    """
    Exception raised when a function signature is not compatible with the
    coresponding function signature found in the contract.
    """


class ProcessNotStarted(PnsBaseException):
    """
    Exception raised when failing to start a process on the process manager
    """


class BindError(PnsBaseException):
    """
    Exception raised when arguments for a function in a ContractedContext cannot be bound
    Indicates invalid function arguments.
    """


class PreContractFailed(PnsBaseException):
    """
    Exception raised when a pre contract returns False or False and a message.
    Indicates that the corresponding function could not be called.
    """
