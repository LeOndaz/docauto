import inspect
import re
from typing import Optional
from collections.abc import Mapping, Iterable


def is_text_within_context(
    source_code: str, context_length: Optional[int] = None, model: str = 'gpt-3.5-turbo'
) -> bool:
    """
    Validate if text fits within specified token limit using tiktoken.

    Args:
        source_code: Python source code to check
        context_length: Maximum allowed tokens (None disables check)
        model: OpenAI model name for tokenization

    Returns:
        bool: True if under limit or no limit specified

    Raises:
        ImportError: If tiktoken not installed
        ValueError: For unsupported models
    """
    try:
        import tiktoken
    except ImportError:
        raise ImportError("Required: 'pip install tiktoken'")

    try:
        encoder = tiktoken.encoding_for_model(model)
    except KeyError:
        # resort to gpt-4o for now, idk what's the correct fallback
        encoder = tiktoken.encoding_for_model('gpt-4o')

    token_count = len(encoder.encode(source_code))

    if context_length is not None:
        return token_count <= context_length
    return True


def get_obj_source(obj):
    """
    Retrieve source code with validation.

    Args:
        obj (callable): Callable to get source code
    Returns:
        str: Raw source code
    Raises:
        ValueError: For invalid inputs
    """
    if not callable(obj):
        raise ValueError('Input must be a callable, got {0}'.format(type(callable)))

    try:
        return inspect.getsource(obj)
    except (OSError, TypeError) as e:
        if inspect.isbuiltin(obj):
            raise ValueError('Cannot document built-in/C-extension objects') from e
        raise ValueError('Source code unavailable') from e


def remove_markdown_fences(response: str) -> str:
    """Remove markdown code block fences from the response."""
    return re.sub(
        r'^```(?:\w+)?\s*\n|\n```(?:\w+)?\s*$', '', response, flags=re.MULTILINE
    )


def remove_function_definition(response: str) -> str:
    """Remove any function definition that might be included in the response."""
    return re.sub(r'^def\s+\w+\([^)]*\):', '', response, count=1, flags=re.MULTILINE)


def extract_docstring_content(response: str) -> str:
    """Extract the content between triple quotes."""
    pattern = re.compile(r'(?P<quote>\'\'\'|""")(?P<doc>.*?)(?P=quote)', re.DOTALL)
    match = pattern.search(response)

    if not match:
        return response

    return match.group('doc')


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
