import logging
from abc import ABC, abstractmethod

import openai
import tiktoken

from docauto.config import GenerationConfig
from docauto.exceptions import GenerationError
from docauto.models import LLMDocstringResponse
from docauto.types import GenerationOptions

try:
    from typing import Unpack
except ImportError:
    from typing_extensions import Unpack


class BaseDocsGenerator(ABC):
    """Base documentation generator."""

    config_class = GenerationConfig

    @abstractmethod
    def __init__(
        self,
        client: openai.OpenAI,
        *,
        logger: logging.Logger = None,
        **options: Unpack[GenerationOptions],
    ):
        self.logger = logger
        self.client = client
        self.min_response_context = 5000
        self.config = self.config_class(**options)

    @abstractmethod
    def generate(self, source, context=None):
        pass


class DocAutoGenerator(BaseDocsGenerator):
    """Python function documentation generator with minimal preprocessing"""

    def __init__(
        self,
        client: openai.OpenAI,
        *,
        logger: logging.Logger = None,
        **config: Unpack[GenerationOptions],
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
            client,
            logger=logger or logging.getLogger('docauto'),
            **config,
        )

    def generate(self, source, context=None):
        """
        Generate documentation for a function.

        Args:
            source (callable): Function to document
            context (str): Additional context for documentation

        Returns:
            str: Generated documentation

        Raises:
            GenerationError: If documentation generation fails
        """
        if not isinstance(source, str):
            raise TypeError(
                f'source parameter can only of type string, received {type(source)}'
            )

        if source == '':
            raise ValueError('source parameter cannot be empty')

        try:
            prompt = self._build_prompt(source, context)
            return self._generate_documentation(prompt)
        except openai.OpenAIError as e:
            self.logger.error('Documentation generation failed: %s', str(e))
            raise GenerationError('Failed to generate documentation') from e

    def _build_prompt(self, source, context: str = None):
        """Construct a compact LLM prompt"""
        prompt_lines = ['```python', source.strip(), '```']

        if context:
            prompt_lines.append('Additional context: {0}'.format(context))

        prompt = '\n'.join(prompt_lines)
        trimmed_prompt = prompt[: self.config.prompt_length_limit]

        if len(trimmed_prompt) < len(prompt):
            self.logger.warning(
                'Prompt was trimmed from %d to %d characters to fit context window',
                len(prompt),
                len(trimmed_prompt),
            )

        return trimmed_prompt

    def generate_system_prompt(self):
        user_provided_constraints = '\n'.join(self.config.constraints)

        return f"""
            You're a professional documentation writer.

            You'll be provided with a function/class sourcecode to document.
            The user will likely provide a format, stick to it.

            You're to only to respond within the constraints below.
            
            System constraints:
            1. You keep it short, precise and accurate. 
            2. You don't ask questions.
            3. You don't make any assumptions. You use only the facts you're provided.
			4. Don't respond with the docstring quotes.
            5. Respond in spihx docstring format if the user doesn't provide a format.
            
            User constraints:
                {user_provided_constraints}

            Anything that doesn't match the constraints should be rejected explicitly 
            and mention exactly which constraint was validated.
        """

    def _generate_documentation(self, prompt):
        """Execute the LLM documentation generation"""
        system_prompt = self.generate_system_prompt()
        tokenizer = self.get_tokenizer()
        tokens = tokenizer.encode(f'{system_prompt}\n{prompt}\n')

        if len(tokens) > (self.config.max_context - self.min_response_context):
            raise ValueError('Prompt exceeds max_context limit.')

        remaining_tokens_count = self.config.max_context - len(tokens)

        response = self.client.beta.chat.completions.parse(
            model=self.config.ai_model,
            messages=[
                {'role': 'system', 'content': self.generate_system_prompt()},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.3,
            max_tokens=remaining_tokens_count,
            response_format=LLMDocstringResponse,
        )
        return response.choices[0].message.content

    def get_encoding(self):
        return 'cl100k_base'

    def get_tokenizer(self):
        return tiktoken.get_encoding(self.get_encoding())
