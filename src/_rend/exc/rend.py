class RendBaseError(Exception):
    """
    Base Exception for the render system
    """


class RendPipeError(RendBaseError):
    """
    Exception raised when a render pipe is not define or available
    """


class RenderError(RendBaseError):
    """
    Exception raised when a renderer raises an explicit error
    """
