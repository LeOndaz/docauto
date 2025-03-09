import pytest
from docugen.generator import DocuGen


@pytest.fixture
def generator():
    """Create a DocuGen instance for testing"""
    return DocuGen(base_url='http://localhost:11434')
