import pytest

from docauto.generator import DocAutoGenerator


@pytest.fixture
def generator():
    """Create a DocAuto instance for testing"""
    return DocAutoGenerator(base_url='http://localhost:11434')
