import pytest
from openai import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from docauto.exceptions import GenerationError
from docauto.generator import DocAutoGenerator


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


def test_max_context_limit(generator, mock_openai_client, logger):
    """Test handling of source code exceeding max context"""
    generator = DocAutoGenerator(
        mock_openai_client,
        logger=logger,
        max_context=10,
        ai_model='no-need',
    )
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


def test_invalid_constraints(mock_openai_client):
    """Test handling of invalid constraints type"""
    with pytest.raises(TypeError):
        DocAutoGenerator(
            mock_openai_client,
            max_context=10000,
            ai_model='no-need',
            constraints='invalid_constraints_type',  # noqa (the typehinting catches it)
        )


def test_malformed_llm_response(mock_openai_client, generator):
    """Test handling of malformed LLM responses"""
    mock_openai_client.beta.chat.completions.parse.side_effect = OpenAIError(
        'Malformed response'
    )

    with pytest.raises(GenerationError, match='Failed to generate documentation'):
        generator.generate('def test(): pass')
