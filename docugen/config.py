from types import MappingProxyType
from typing import List, Optional, TypedDict
from pydantic import BaseModel, Field


class Config(TypedDict):
    """Type-safe configuration for documentation generation"""

    base_url: str
    ai_model: str
    api_key: Optional[str]
    max_context: int
    constraints: List[str]


class LLMDocstringSingleResponse(BaseModel):
    """Structured output model for a single LLM-generated docstring"""
    
    content: str = Field(description="The generated docstring content")
    format: str = Field(default="sphinx", description="The format of the docstring (e.g. sphinx, google)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata about the generation")


class LLMDocstringResponse(BaseModel):
    """Container model for multiple LLM-generated docstrings"""
    
    responses: List[LLMDocstringSingleResponse] = Field(description="List of generated docstring responses")
    metadata: dict = Field(default_factory=dict, description="Additional metadata about the overall generation")


def create_config(
    base_url: str,
    ai_model: str,
    api_key: Optional[str] = None,
    max_context: int = 8192,
    constraints: Optional[List[str]] = None,
) -> MappingProxyType:
    """Create an immutable configuration dictionary"""
    if constraints is None:
        constraints = [
            "Don't respond with anything other than code",
            """
                Strictly respond in Sphinx documentation format.
                Here's an example that uses sphinx:

                :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
                :type [ParamName]: [ParamType](, optional)
                ...
                :raises [ErrorType]: [ErrorDescription]
                ...
                :return: [ReturnDescription]
                :rtype: [ReturnType]

                A pair of :param: and :type: directive options must be used for each parameter we wish to document. The :raises: option is used to describe any errors that are raised by the code, while the :return: and :rtype: options are used to describe any values returned by our code. A more thorough explanation of the Sphinx docstring format can be found here.

                Note that the ... notation has been used above to indicate repetition and should not be used when generating actual docstrings, as can be seen by the example presented below.
            """,
            'Provide a usage example unless stated otherwise.',
            'Your respond will be taken as a docstring. Respond only with docstrings.',
        ]

    return MappingProxyType({
        'base_url': base_url,
        'ai_model': ai_model,
        'api_key': api_key,
        'max_context': max_context,
        'constraints': constraints,
    })


OLLAMA_PRESET = create_config(
    base_url='http://localhost:11434/v1',
    ai_model='phi4',
    api_key='ollama',
    max_context=16384,
)

OPENAI_PRESET = create_config(
    base_url='https://api.openai.com/v1',
    ai_model='gpt-3.5-turbo',
    max_context=16384,
)
