from collections.abc import Iterable, Mapping


def is_valid_string_iterable(obj: Iterable) -> bool:
    """Validate if an input is a valid iterable of strings.

    Args:
        obj: Object to validate

    Returns:
        bool: True if obj is None or an iterable of strings (excluding bytes, str, dict)
    """
    if obj is None:
        return True

    if isinstance(obj, (str, bytes, Mapping)):
        return False

    if not isinstance(obj, Iterable):
        return False

    return all(isinstance(item, str) for item in obj)
