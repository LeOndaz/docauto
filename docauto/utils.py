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


def get_all_dunder_methods():
    """
    Returns a list of all dunder methods (attributes starting and ending with __)
    for the given object or class.

    Note that __init__ is included, we document class.__init__ on the class level.
    """

    class Object:
        pass

    obj = Object()
    return {name for name in dir(obj) if name.startswith('__') and name.endswith('__')}


all_dunder_methods = get_all_dunder_methods()
