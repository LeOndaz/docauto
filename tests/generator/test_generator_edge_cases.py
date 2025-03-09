import pytest
from unittest.mock import patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from docugen.generator import DocuGen


@pytest.fixture
def mock_malformed_response():
    return ChatCompletion(
        id='test_id',
        model='gpt-3.5-turbo',
        object='chat.completion',
        created=1234567890,
        choices=[
            Choice(
                finish_reason='stop',
                index=0,
                message=ChatCompletionMessage(
                    content='{"responses": [{"content": "Invalid JSON"}]}',
                    role='assistant'
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
    with pytest.raises(ValueError, match='prompt is too long'):
        generator.generate('def very_long_function(): pass')


def test_failed_llm_response(mock_openai_client, generator):
    """Test handling of failed LLM API calls"""
    mock_openai_client.chat.completions.create.side_effect = Exception('API Error')

    with pytest.raises(RuntimeError, match='Failed to generate documentation'):
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


def test_malformed_llm_response(mock_malformed_response):
    """Test handling of malformed LLM responses"""
    with patch('openai.OpenAI') as mock_client:
        instance = mock_client.return_value
        instance.chat.completions.create.return_value = mock_malformed_response

        generator = DocuGen(base_url='http://localhost:11434')
        result = generator.generate('def test(): pass')

        # The sanitizer chain should handle malformed responses gracefully
        assert isinstance(result, str)
        assert len(result) > 0
