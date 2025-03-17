import reprlib
from dataclasses import dataclass, field, fields
from typing import List, Optional
from urllib.parse import urlparse

from docauto.types import DocAutoOptions
from docauto.utils import all_dunder_methods

try:
    from typing import Unpack
except ImportError:
    from typing_extensions import Unpack

__all__ = (
    'DocAutoConfig',
    'APIConfig',
    'GenerationConfig',
    'default_constraints',
    'default_ignore_patterns',
)

default_constraints = [
    "Don't respond with anything other than valid code",
    """
            Strictly respond in Sphinx documentation format.
            Here's an example that uses sphinx:

            \"\"\"Summary line.

            :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
            :type [ParamName]: [ParamType](, optional)
            ...
            :raises [ErrorType]: [ErrorDescription]
            ...
            :return: [ReturnDescription]
            :rtype: [ReturnType]
            \"\"\"

            A pair of :param: and :type: directive options must be used for each parameter we wish to document. The :raises: option is used to describe any errors that are raised by the code, while the :return: and :rtype: options are used to describe any values returned by our code. A more thorough explanation of the Sphinx docstring format can be found here.

            Note that the ... notation has been used above to indicate repetition and should not be used when generating actual docstrings, as can be seen by the example presented below.

            If there're no params, ignore the params section.
            If there're no returned objects, ignore the :return.
        """,
    'Single line docstrings should not end with any spacing',
]

default_ignore_patterns = {
    *all_dunder_methods,
}


@dataclass(frozen=True)
class APIConfig:
    """Configuration for API settings with built-in validation.

    :param base_url: The base URL for the API endpoint
    :type base_url: str
    :param api_key: Optional API key for authentication
    :type api_key: Optional[str]
    """

    base_url: str
    api_key: str

    def __post_init__(self):
        if not self.base_url:
            raise ValueError('Base URL is required')

        if not self.api_key:
            raise ValueError('API key required')

        # Validate URL format
        try:
            result = urlparse(self.base_url)
            if not all([result.scheme, result.netloc]):
                raise ValueError
        except ValueError:
            raise ValueError(f'Invalid base URL format: {self.base_url}')


@dataclass(frozen=True)
class GenerationConfig:
    """Configuration for documentation generation settings.

    :param constraints: List of constraints for documentation generation
    :type constraints: List[str]
    """

    ai_model: str
    max_context: int = 16384

    constraints: List[str] = field(
        default_factory=lambda: default_constraints,
    )
    ignore_patterns: List[str] = field(default_factory=lambda: default_ignore_patterns)
    prompt_length_limit: int = field(default_factory=lambda: 10_000)

    def __post_init__(self):
        if not self.ai_model:
            raise ValueError('AI model is required')

        if not self.constraints:
            raise ValueError('At least one constraint is required')

        # tied to the list, for now since I'm using `append` somewhere
        if not isinstance(self.constraints, list):
            raise TypeError('constraints must be a list')

        # Should make sense, at some point
        if self.max_context < 1:
            raise ValueError('max_context must be positive')

    def __repr__(self):
        r = reprlib.Repr()
        r.maxlist = 2
        r.maxstring = 50

        field_reprs = []
        for f in fields(self):
            value = getattr(self, f.name)
            repr_value = r.repr(value)
            field_reprs.append(f'{f.name}={repr_value}')

        return f'{self.__class__.__name__}({", ".join(field_reprs)})'


@dataclass(frozen=True)
class DocAutoConfig:
    """Complete configuration combining API and generation settings.

    :param api: API configuration settings
    :type api: APIConfig
    :param generation: Documentation generation settings
    :type generation: GenerationConfig
    """

    api: APIConfig
    generation: Optional[GenerationConfig]

    @classmethod
    def create(
        cls,
        **data: Unpack[DocAutoOptions],
    ) -> 'DocAutoConfig':
        """Factory method to create a new configuration instance.

        :return: A new DocAutoConfig instance
        :rtype: DocAutoConfig
        """
        api_config = APIConfig(**data.get('api', {}))
        generation_config = GenerationConfig(**data.get('generation', {}))
        return cls(api=api_config, generation=generation_config)
