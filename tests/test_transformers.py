import libcst as cst

from docauto.models import LLMDocstringResponse, LLMDocstringSingleResponse
from docauto.parsers import LLMDocstringResponseParser


def test_transformer_initialization(transformer):
    """Test transformer initialization with default settings."""
    assert transformer.overwrite is True
    assert isinstance(transformer.parser, LLMDocstringResponseParser)


def test_needs_docstring_no_existing(transformer):
    """Test needs_docstring when no docstring exists."""
    node = cst.parse_module('def test(): pass').body[0]
    assert transformer.needs_docstring(node) is True


def test_needs_docstring_existing(transformer):
    """Test needs_docstring when docstring exists."""
    node = cst.parse_module('def test():\n    """Existing docstring"""\n    pass').body[
        0
    ]
    assert transformer.needs_docstring(node) is transformer.overwrite


def test_generate_docstring(transformer, test_function_sourcecode):
    """Test docstring generation for a function."""
    node = cst.parse_module(test_function_sourcecode).body[0]
    docstring = transformer.generate_docstring(node)
    assert isinstance(docstring, str)
    assert len(docstring) > 0


def test_format_docstring(transformer):
    """Test docstring formatting with LLM response."""
    llm_response_content_1 = LLMDocstringSingleResponse(
        content='Test docstring',
        format='sphinx',
        should_indent=False,
        should_indent_first_line=False,
        should_add_newline_at_the_end=True,
    )
    llm_response = LLMDocstringResponse(responses=[llm_response_content_1])
    node = cst.parse_module('def test(): pass').body[0]
    formatted = transformer.format_docstring(llm_response, node, node)
    assert isinstance(formatted, str)
    assert '"""' in formatted


def test_class_context_tracking(transformer, test_class_sourcecode):
    """Test class context tracking during transformation."""
    module = cst.parse_module(test_class_sourcecode)
    transformer.visit_ClassDef(module.body[0])


def test_progress_tracking(transformer, progress_tracker, test_function_sourcecode):
    """Test progress tracking during transformation."""
    transformer.progress_tracker = progress_tracker
    module = cst.parse_module(test_function_sourcecode)
    transformer.visit_FunctionDef(module.body[0])
    assert len(progress_tracker.tracked_object['current_file']) > 0


def test_transform_with_existing_docstring(transformer):
    """Test transformation of code with existing docstring."""
    code = 'def test():\n    """Existing docstring"""\n    pass'
    transformer.overwrite = False
    module = cst.parse_module(code)
    result = module.visit(transformer)
    assert result.code == code  # Should not modify when overwrite=False


def test_transform_class_method(transformer, test_class_sourcecode):
    """Test transformation of a class method."""
    module = cst.parse_module(test_class_sourcecode)
    result = module.visit(transformer)
    assert isinstance(result, cst.Module)
    assert any(isinstance(node, cst.ClassDef) for node in result.body)


def test_error_handling(transformer):
    """Test error handling during transformation."""
    node = cst.parse_module('def test(): pass').body[0]
    transformer.generator.generate = lambda *args, **kwargs: None  # Force error
    result = transformer._process_node(node, node)
    assert result == node  # Should return original node on error
