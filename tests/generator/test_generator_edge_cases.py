from unittest.mock import patch

import pytest
from openai import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from docugen.exceptions import GenerationError
from docugen.generator import DocuGen


@pytest.fixture
def mock_malformed_response():
    return ChatCompletion(
        id='test_id',
        model='gpt-4o-mini',
        object='chat.completion',
        created=1234567890,
        choices=[
            Choice(
                finish_reason='stop',
                index=0,
                message=ChatCompletionMessage(
                    content='{"responses": [{"content": "Test docstring", "format": "sphinx", "should_indent": true, "should_indent_first_line": false, "should_add_newline_at_the_end": false}], "invalid_field": "This should cause parsing error"}',
                    role='assistant',
                ),
            )
        ],
    )


def test_empty_source(generator):
    """Test handling of empty source code"""
    with pytest.raises(ValueError):
        generator.generate('')


def test_max_context_limit():
    """Test handling of source code exceeding max context"""
    generator = DocuGen(base_url='http://localhost:11434', max_context=10)
    generator.min_response_context = 0

    with pytest.raises(ValueError, match='Prompt exceeds max_context limit.'):
        generator.generate('def very_long_function(): pass')


def test_failed_llm_response(mock_openai_client, generator):
    """Test handling of failed LLM API calls"""

    mock_openai_client.beta.chat.completions.parse.side_effect = OpenAIError(
        'API Error'
    )

    with pytest.raises(GenerationError, match='Failed to generate documentation'):
        generator.generate('def test(): pass')


def test_invalid_api_key():
    """Test initialization with invalid API key for non-local setup"""
    with pytest.raises(ValueError, match='API key is required'):
        DocuGen(base_url='https://api.openai.com/v1')


def test_invalid_constraints():
    """Test handling of invalid constraints type"""
    with pytest.raises(TypeError):
        DocuGen(
            base_url='http://localhost:11434', constraints='invalid_constraints_type'
        )


def test_malformed_llm_response(mock_openai_client, generator):
    """Test handling of malformed LLM responses"""
    mock_openai_client.beta.chat.completions.parse.side_effect = OpenAIError(
        'Malformed response'
    )

    with pytest.raises(GenerationError, match='Failed to generate documentation'):
        generator.generate('def test(): pass')
