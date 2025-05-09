from docauto.generator import DocAutoGenerator
from docauto.models import LLMDocstringResponse, LLMDocstringSingleResponse


def test_docauto_initialization(mock_openai_client):
    """Test DocAutoCLI initialization with valid parameters"""
    generator = DocAutoGenerator(
        mock_openai_client,
        ai_model='gpt-4o-mini',
        max_context=1000,
        constraints=['test constraint'],
    )

    assert generator.config.ai_model == 'gpt-4o-mini'
    assert generator.config.max_context == 1000
    assert generator.config.constraints == ['test constraint']


def test_docauto_local_initialization(mock_openai_client):
    """Test DocAutoCLI initialization with local setup (no API key required)"""
    generator = DocAutoGenerator(
        client=mock_openai_client, max_context=10000, ai_model='phi4'
    )
    assert generator.config.ai_model == 'phi4'
    assert generator.config.max_context == 10000


def test_system_prompt_generation(mock_openai_client):
    """Test system prompt generation with various constraints"""
    generator = DocAutoGenerator(
        mock_openai_client,
        constraints=['Test constraint 1', 'Test constraint 2'],
        max_context=10000,
        ai_model='no-need',
    )

    system_prompt = generator.generate_system_prompt()
    assert 'Test constraint 1' in system_prompt
    assert 'Test constraint 2' in system_prompt


def test_additional_context_handling(mock_openai_client):
    """Test handling of additional context in prompt generation"""
    generator = DocAutoGenerator(
        mock_openai_client,
        constraints=['Test constraint 1', 'Test constraint 2'],
        max_context=10000,
        ai_model='no-need',
    )
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
    assert isinstance(response_1.content, str)
    assert isinstance(llm_response.responses, list)
    assert isinstance(llm_response.responses[0], LLMDocstringSingleResponse)
    assert isinstance(llm_response.responses[0].content, str)
    assert llm_response.responses[0].content == 'Test docstring'
