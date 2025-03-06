class InvalidPythonModule(Exception):
    """
    An exception raised when a Python module has invalid syntax.
    """

    def __init__(self, original_exception):
        self.original_exception = original_exception

    def __str__(self) -> str:
        return self.original_exception
