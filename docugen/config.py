from types import MappingProxyType
from typing import List, Optional, TypedDict


class APIConfig(TypedDict):
    """Type-safe configuration for documentation generation"""

    base_url: str
    ai_model: str
    api_key: Optional[str]
    max_context: int
    constraints: List[str]


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

    return MappingProxyType(
        {
            'base_url': base_url,
            'ai_model': ai_model,
            'api_key': api_key,
            'max_context': max_context,
            'constraints': constraints,
        }
    )


OLLAMA_PRESET = create_config(
    base_url='http://localhost:11434/v1',
    ai_model='phi4',
    api_key='ollama',
    max_context=16384,
)

OPENAI_PRESET = create_config(
    base_url='https://api.openai.com/v1',
    ai_model='gpt-4o-mini',
    max_context=16384,
)

GEMINI_PRESET = create_config(
    base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
    ai_model='gemini-2.0-flash-exp',  # this is a free API
    max_context=131_072,
)

DEEPSEEK_PRESET = create_config(
    base_url='https://api.deepseek.com/v1',
    ai_model='deepseek-chat',
    max_context=65_536,
)
