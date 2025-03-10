import logging


class SmartFormatter(logging.Formatter):
    def __init__(self, default_format, exc_format=None):
        """
        Initialize the formatter.

        Args:
            default_format (str): The format string to use when no exception is present.
            exc_format (str): The format string to use when an exception is present.
                              If None, appends `%(exc_info)s` to the default format.
        """
        super().__init__(fmt=default_format, datefmt=None, style='%')
        self.default_format = default_format
        self.exc_format = (
            exc_format if exc_format is not None else default_format + ' %(exc_info)s'
        )

    def format(self, record):
        """
        Format the specified record. If an exception is present, use the exception format.
        Otherwise, use the default format.
        """
        # Save the original format
        original_format = self._style._fmt

        # Use the exception format if there's exception info
        if record.exc_info:
            self._style._fmt = self.exc_format
        else:
            self._style._fmt = self.default_format

        # Format the record
        result = super().format(record)

        # Restore the original format
        self._style._fmt = original_format

        return result
