from docugen.generator import DocuGen
from docugen.models import LLMDocstringResponse, LLMDocstringSingleResponse


def test_docugen_initialization():
    """Test DocuGen initialization with valid parameters"""
    generator = DocuGen(
        base_url='http://localhost:11434',
        api_key='test_key',
        ai_model='gpt-3.5-turbo',
        max_context=1000,
        constraints=['test constraint'],
    )

    assert generator.config['base_url'] == 'http://localhost:11434'
    assert generator.config['api_key'] == 'test_key'
    assert generator.config['ai_model'] == 'gpt-3.5-turbo'
    assert generator.config['max_context'] == 1000
    assert generator.config['constraints'] == ['test constraint']


def test_docugen_local_initialization():
    """Test DocuGen initialization with local setup (no API key required)"""
    generator = DocuGen(base_url='http://localhost:11434')
    assert generator.client.api_key == 'ollama'


def test_system_prompt_generation():
    """Test system prompt generation with various constraints"""
    generator = DocuGen(
        base_url='http://localhost:11434',
        constraints=['Test constraint 1', 'Test constraint 2'],
    )

    system_prompt = generator.generate_system_prompt()
    assert 'Test constraint 1' in system_prompt
    assert 'Test constraint 2' in system_prompt


def test_additional_context_handling(mock_openai_client):
    """Test handling of additional context in prompt generation"""
    generator = DocuGen(base_url='http://localhost:11434')
    response = generator.generate('def test(): pass', context='Test context')
    assert isinstance(response, str)
    assert len(response) > 0

    called_prompt = mock_openai_client.beta.chat.completions.parse.call_args[1][
        'messages'
    ][1]['content']
    assert 'Test context' in called_prompt


def test_response_single_entity_parsing():
    """Test parsing of LLM response into structured format"""
    response = LLMDocstringSingleResponse(content='Test docstring')
    assert isinstance(response.content, str)
    assert response.content == 'Test docstring'


def test_response_multiple_parsing():
    """Test parsing of LLM response into structured format"""
    response_1 = LLMDocstringSingleResponse(content='Test docstring')
    llm_response = LLMDocstringResponse(responses=[response_1])
    assert isinstance(LLMDocstringSingleResponse.content, str)
    assert isinstance(llm_response.responses, list)
    assert isinstance(llm_response.responses[0], LLMDocstringSingleResponse)
    assert isinstance(llm_response.responses[0].content, str)
    assert llm_response.responses[0].content == 'Test docstring'
