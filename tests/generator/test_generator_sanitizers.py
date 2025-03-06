import pytest
from docugen.generator import DocuGen
from docugen.utils import (
    extract_docstring_content,
    remove_function_definition,
    remove_markdown_fences,
)


@pytest.fixture
def generator():
    """Create a DocuGen instance for testing"""
    return DocuGen(base_url='http://localhost:11434')


def test_sanitizer_chain_order(generator):
    """Test that sanitizers are applied in the correct order"""
    test_input = '```plaintext\n    def test():\n        pass\n    Test content\n```'
    expected_output = 'Test content'

    # Apply each sanitizer in the chain manually
    result = test_input
    for sanitizer in generator.get_response_sanitizers():
        result = generator.call_sanitizer(sanitizer, result)

    assert result == expected_output


def test_individual_sanitizers(generator):
    """Test each sanitizer individually"""
    # Test strip sanitizer
    assert generator.call_sanitizer(str.strip, '  test  ') == 'test'

    # Test markdown fence removal
    assert (
        generator.call_sanitizer(
            {'sanitizer': remove_markdown_fences, 'fail_silent': True},
            '```python\ntest\n```',
        )
        == 'test'
    )

    # Test function definition removal
    assert (
        generator.call_sanitizer(
            {'sanitizer': remove_function_definition, 'fail_silent': True},
            'def test():\n    pass\nactual content',
        )
        == 'actual content'
    )

    # Test docstring content extraction
    assert (
        generator.call_sanitizer(extract_docstring_content, 'Test docstring content')
        == 'Test docstring content'
    )


def test_fail_silent_behavior(generator):
    """Test fail-silent behavior of sanitizers"""
    failing_sanitizer = {
        'sanitizer': lambda x: x.undefined_attribute,  # This will raise AttributeError
        'fail_silent': True,
    }

    # Should return original input when sanitizer fails
    test_input = 'test content'
    assert generator.call_sanitizer(failing_sanitizer, test_input) == test_input


def test_fail_loud_behavior(generator):
    """Test fail-loud behavior of sanitizers"""
    failing_sanitizer = {
        'sanitizer': lambda x: x.undefined_attribute,  # This will raise AttributeError
        'fail_silent': False,
    }

    with pytest.raises(ValueError, match='Sanitizer failed'):
        generator.call_sanitizer(failing_sanitizer, 'test content')


def test_invalid_sanitizer_config(generator):
    """Test handling of invalid sanitizer configurations"""
    invalid_sanitizer = {'invalid_key': lambda x: x}

    with pytest.raises(ValueError, match="Missing 'sanitizer' key"):
        generator.call_sanitizer(invalid_sanitizer, 'test content')


def test_sanitizer_chain_with_complex_input(generator):
    """Test sanitizer chain with complex, multi-line input"""
    complex_input = '''
    ```python
    def complex_function():
        """This is a docstring"""
        pass
    
    Test content with multiple\nlines and special chars: @#$%
    ```
    '''

    result = complex_input
    for sanitizer in generator.get_response_sanitizers():
        result = generator.call_sanitizer(sanitizer, result)

    assert result.strip() == 'Test content with multiple\nlines and special chars: @#$%'


def test_custom_sanitizer_addition(generator):
    """Test adding a custom sanitizer to the chain"""
    def custom_sanitizer(x):
        return x.upper()

    original_sanitizers = generator.get_response_sanitizers()

    # Add custom sanitizer to the chain
    generator.llm_response_sanitizers = [custom_sanitizer] + original_sanitizers

    test_input = '```plaintext\ntest content\n```'
    result = test_input

    for sanitizer in generator.get_response_sanitizers():
        result = generator.call_sanitizer(sanitizer, result)

    assert result == 'TEST CONTENT'


def test_empty_input_handling(generator):
    """Test sanitizer chain with empty or whitespace input"""
    # Test empty string
    assert all(
        generator.call_sanitizer(sanitizer, '') == ''
        for sanitizer in generator.get_response_sanitizers()
    )

    # Test whitespace string
    result = '   \n   '
    for sanitizer in generator.get_response_sanitizers():
        result = generator.call_sanitizer(sanitizer, result)
    assert result == ''
