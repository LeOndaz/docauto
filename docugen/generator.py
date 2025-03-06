import logging
from abc import ABC, abstractmethod
from typing import List, Callable, Optional, TypedDict, Union
from openai import OpenAI

from docugen.config import Config
from docugen.utils import (
    extract_docstring_content,
    is_text_within_context,
    is_valid_string_iterable,
    remove_function_definition,
    remove_markdown_fences
)

class LLMResponseSanitizerDict(TypedDict):
    """TypedDict for sanitizer function."""
    sanitizer: Callable[[str], str]
    fail_silent: Optional[bool] = False

LLMResponseSanitizer = Union[LLMResponseSanitizerDict, Callable]


class BaseDocsGenerator(ABC):
    """Base documentation generator."""

    llm_response_sanitizers: List[LLMResponseSanitizer] = [
        str.strip,
        {
            "sanitizer": remove_markdown_fences,
            "fail_silent": True,
        },
        {
            "sanitizer": remove_function_definition,
            "fail_silent": True,
        },
        extract_docstring_content,
        str.strip,
    ]

    @abstractmethod
    def __init__(
        self,
        base_url='https://api.openai.com/v1',
        ai_model='gpt-3.5-turbo',
        api_key=None,
        max_context=16384,
        constraints=None,
        logger: logging.Logger = None,
    ):
        if not isinstance(base_url, str):
            raise TypeError('base_url must be a string')
        if not isinstance(ai_model, str):
            raise TypeError('ai_model must be a string')
        if api_key is not None and not isinstance(api_key, str):
            raise TypeError('api_key must be a string or None')
        if not isinstance(max_context, int):
            raise TypeError('max_context must be an integer')
        if not is_valid_string_iterable(constraints):
            raise TypeError('constraints must be an iterable of strings (except dict, str, bytes) or None')
        if logger is not None and not isinstance(logger, logging.Logger):
            raise TypeError('logger must be a Logger instance or None')

        self.config: Config = {
            'base_url': base_url,
            'ai_model': ai_model,
            'api_key': api_key,
            'max_context': max_context,
            'constraints': constraints,
        }
        self.is_local = 'localhost' in self.config['base_url']

        if not self.is_local and not self.config['api_key']:
            raise ValueError('API key is required for documentation generation')

        self.logger = logger

    @abstractmethod
    def generate(self, source, additional_context=None):
        pass

    def get_response_sanitizers(self):
        return self.llm_response_sanitizers

    def call_sanitizer(self, sanitizer: LLMResponseSanitizer, llm_response):
        if callable(sanitizer):
            return sanitizer(llm_response)

        elif isinstance(sanitizer, dict):
            if 'sanitizer' not in sanitizer:
                raise ValueError("Missing 'sanitizer' key in sanitizer dictionary")
            
            fail_silent = False

            if "fail_silent" in sanitizer:
                assert type(sanitizer['fail_silent']) is bool
                fail_silent = sanitizer['fail_silent']
            
            try:
                return sanitizer['sanitizer'](llm_response)
            except Exception as e:
                if fail_silent:
                    return llm_response
                raise ValueError(f"Sanitizer failed: {e}") from e


class DocuGen(BaseDocsGenerator):
    """Python function documentation generator with minimal preprocessing"""

    def __init__(
        self,
        base_url='https://api.openai.com/v1',
        ai_model='gpt-3.5-turbo',
        api_key=None,
        max_context=16384,
        constraints=None,
        logger: logging.Logger = None,
    ):
        """
        Initialize the documentation generator.

        Args:
            base_url (str): OpenAI-compatible API endpoint
            api_key (str): API key for authentication
            max_context (int): Maximum context window size
            constraints (list): Documentation constraints

        Raises:
            ValueError: If no API key is provided
        """

        super().__init__(
            base_url=base_url,
            ai_model=ai_model,
            api_key=api_key,
            max_context=max_context,
            constraints=constraints,
            logger=logger or logging.getLogger('docugen')
        )

        self.client = OpenAI(
            base_url=self.config['base_url'],
            api_key=self.config['api_key'] if not self.is_local else 'ollama',
        )

    def generate(self, source, additional_context=None):
        """
        Generate documentation for a function.

        Args:
            source (callable): Function to document
            additional_context (str): Additional context for documentation

        Returns:
            str: Generated documentation

        Raises:
            RuntimeError: If documentation generation fails
        """
        try:
            prompt = self._build_prompt(source, additional_context)

            if not is_text_within_context(
                prompt, self.config['max_context'], self.config['ai_model']
            ):
                raise ValueError('prompt is too long')

            llm_response = self._generate_documentation(prompt)

            for sanitizer in self.get_response_sanitizers():
                llm_response = self.call_sanitizer(sanitizer, llm_response)

            return llm_response
        except Exception as e:
            self.logger.error('Documentation generation failed: %s', str(e))
            raise RuntimeError('Failed to generate documentation') from e

    def _build_prompt(self, source, additional_context):
        """Construct a compact LLM prompt"""
        prompt_lines = ['```python', source.strip(), '```']

        if additional_context:
            prompt_lines.append('Additional context: {0}'.format(additional_context))

        return '\n'.join(prompt_lines)[: self.config['max_context']]

    def generate_system_prompt(self):
        user_provided_constraints = '\n'.join(self.config['constraints'])

        return f"""
            You're a professional documentation writer.

            You'll be provided with a function/class sourcecode to document.
            The user will likely provide a format, stick to it. If not, use python sphinx format
			for docstrings.

            You're to only to respond within the constraints below.
            
            System constraints:
            1. You keep it short, precise and accurate. 
            2. You don't ask questions.
            3. You don't make any assumptions. You use only the facts you're provided.
			4. You respond with a markdown block of code ```plaintext[TEXT_HERE]\n``` that has the  docstring text, without docstring quotes.
            5. Respond in spihx docstring format if the usert doesn't provide a format.
            
            User constraints:
                {user_provided_constraints}

            Anything that doesn't match the constraints should be rejected explicitly 
            and mention exactly which constraint was validated.
        """

    def _generate_documentation(self, prompt):
        """Execute the LLM documentation generation"""
        try:
            response = self.client.chat.completions.create(
                model=self.config['ai_model'],
                messages=[
                    {'role': 'system', 'content': self.generate_system_prompt()},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.3,
                max_tokens=self.config['max_context'],
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error('LLM API call failed: %s', str(e))
            raise

