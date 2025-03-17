from collections.abc import Callable
from typing import List, Set, Union

import libcst as cst

try:
    from typing import NotRequired, Required
except ImportError:
    from typing_extensions import NotRequired, Required

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class APIOptions(TypedDict):
    """TypedDict matching APIConfig dataclass.

    :param base_url: The base URL for the API endpoint
    :type base_url: str
    :param api_key: Optional API key for authentication
    :type api_key: str
    """

    base_url: Required[str]
    api_key: str


class GenerationOptions(TypedDict):
    """TypedDict matching GenerationConfig dataclass.

    :param constraints: List of constraints for documentation generation
    :type constraints: List[str]
    :param ignore_patterns: List of patterns to ignore during generation
    :type ignore_patterns: List[str]
    """

    constraints: NotRequired[List[str]]
    ignore_patterns: NotRequired[List[str]]
    prompt_length_limit: NotRequired[int]
    max_context: Required[int]
    ai_model: Required[str]


class DocAutoOptions(TypedDict):
    """TypedDict matching DocAutoConfig dataclass.

    :param api: API configuration settings
    :type api: APIConfigDict
    :param generation: Documentation generation settings
    :type generation: GenerationConfigDict
    """

    api: Required[APIOptions]
    generation: NotRequired[GenerationOptions]


# Hashable callables
IgnorePattern = Union[str, Callable[[cst.CSTNode], bool]]
IgnorePatterns = Set[IgnorePattern]
