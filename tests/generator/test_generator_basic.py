from docugen.generator import DocuGen


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
    generator.generate('def test(): pass', additional_context='Test context')

    called_prompt = mock_openai_client.chat.completions.create.call_args[1]['messages'][
        1
    ]['content']
    assert 'Test context' in called_prompt
