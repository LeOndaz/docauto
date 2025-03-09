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
