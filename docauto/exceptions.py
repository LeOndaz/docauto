class InvalidPythonModule(Exception):
    """
    An exception raised when a Python module has invalid syntax.
    """

    def __init__(self, original_exception):
        self.original_exception = original_exception

    def __str__(self) -> str:
        return str(self.original_exception)


class GenerationError(Exception):
    """
    An exception raised when an error occurs during code generation.
    """

    def __init__(self, original_exception):
        self.original_exception = original_exception

    def __str__(self) -> str:
        return str(self.original_exception)
