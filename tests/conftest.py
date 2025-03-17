import logging

from docauto.presets import PresetManager
from docauto.services import DocumentationService

try:
    from typing import Generator
except ImportError:
    from typing_extensions import Generator

from pathlib import Path
from unittest.mock import patch

import openai
import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from docauto.cli import DocAutoCLI
from docauto.config import APIConfig, DocAutoConfig, GenerationConfig
from docauto.fs import FileSystemService
from docauto.generator import DocAutoGenerator
from docauto.logger import SmartFormatter
from docauto.parsers import LLMDocstringResponseParser
from docauto.tracker import ProgressTracker
from docauto.transformers import DocTransformer


@pytest.fixture
def mock_openai_response():
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
                    content='```plaintext\nTest docstring content\n```',
                    role='assistant',
                ),
            )
        ],
    )


@pytest.fixture
def mock_openai_client(mock_openai_response) -> Generator[openai.OpenAI, None, None]:
    with patch('openai.OpenAI') as mock_client:
        instance = mock_client.return_value
        instance.beta.chat.completions.parse.return_value = mock_openai_response
        yield instance


class TrackedFileSystem(FileSystemService):
    def __init__(self, logger=None) -> None:
        super().__init__(logger)
        self.reads = []
        self.writes = []
        self.found_files = []
        self.resolved_paths = []

    def read_file(self, path: Path) -> str:
        self.reads.append(path)
        return super().read_file(path)

    def write_file(self, path: Path, content: str) -> None:
        self.writes.append((path, content))
        super().write_file(path, content)

    def find_python_files(self, directory: Path):
        for file_path in super().find_python_files(directory):
            self.found_files.append(file_path)
            yield file_path

    def resolve_paths(self, paths):
        for path in super().resolve_paths(paths):
            self.resolved_paths.append(path)
            yield path


@pytest.fixture
def logger():
    handler = logging.StreamHandler()
    formatter = SmartFormatter(
        default_format='[%(levelname)s] [%(asctime)s] [%(name)s]: %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger('test_docauto')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


@pytest.fixture
def generator(mock_openai_client, logger, config):
    # use a better serialization way
    return DocAutoGenerator(
        client=mock_openai_client,
        logger=logger,
        ai_model=config.generation.ai_model,
        constraints=config.generation.constraints,
        max_context=config.generation.max_context,
        ignore_patterns=config.generation.ignore_patterns,
        prompt_length_limit=config.generation.prompt_length_limit,
    )


@pytest.fixture
def parser():
    return LLMDocstringResponseParser()


@pytest.fixture
def file_system(logger):
    return TrackedFileSystem(logger)


@pytest.fixture
def docs_service(generator, logger, file_system):
    return DocumentationService(
        generator=generator,
        fs_service=file_system,
        logger=logger,
    )


@pytest.fixture
def cli(logger, file_system):
    """Fixture for creating a DocAutoCLI instance."""
    return DocAutoCLI(file_system, logger)


@pytest.fixture
def files_for_testing():
    directory = Path('./tests') / 'files_for_testing'
    return directory.iterdir()


@pytest.fixture
def config() -> DocAutoConfig:
    return DocAutoConfig(
        api=APIConfig(
            base_url='http://localhost:11434/v1',
            api_key='ollama',
        ),
        generation=GenerationConfig(
            ai_model='phi4',
            max_context=16384,
            constraints=[
                'Your respond will be taken as a docstring. Respond only with docstrings.',
                'Keep it short, precise and use sphinx format.',
            ],
        ),
    )


@pytest.fixture
def preset_manager():
    return PresetManager()


@pytest.fixture
def transformer(generator, logger, parser):
    """Fixture for creating a DocTransformer instance."""
    return DocTransformer(
        generator=generator,
        logger=logger,
        parser=parser,
        overwrite=True,
    )


@pytest.fixture
def progress_tracker(logger):
    """Fixture for creating a ProgressTracker instance."""
    return ProgressTracker(logger)


@pytest.fixture
def test_function_sourcecode():
    """Fixture providing a sample function for testing."""

    return """
def calculate_sum(a: int, b: int) -> int:
    return a + b
"""


@pytest.fixture
def test_class_sourcecode():
    """Fixture providing a sample class for testing."""
    return """
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
"""


@pytest.fixture(autouse=True)
def remove_test_file_docstrings(logger):
    """Fixture that automatically removes docstrings from test files before each test."""
    from pathlib import Path

    import libcst as cst

    class DocstringRemover(cst.CSTTransformer):
        def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
        ) -> cst.ClassDef:
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=[
                        stmt
                        for stmt in updated_node.body.body
                        if not isinstance(stmt, cst.SimpleStatementLine)
                        or not any(
                            isinstance(elem, cst.Expr)
                            and isinstance(elem.value, cst.SimpleString)
                            for elem in stmt.body
                        )
                    ]
                )
            )

        def leave_FunctionDef(
            self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
        ) -> cst.FunctionDef:
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=[
                        stmt
                        for stmt in updated_node.body.body
                        if not isinstance(stmt, cst.SimpleStatementLine)
                        or not any(
                            isinstance(elem, cst.Expr)
                            and isinstance(elem.value, cst.SimpleString)
                            for elem in stmt.body
                        )
                    ]
                )
            )

    test_files_dir = Path(__file__).parent / 'files_for_testing'
    transformer = DocstringRemover()

    for file_path in test_files_dir.glob('*.py'):
        try:
            source = file_path.read_text()
            tree = cst.parse_module(source)
            modified = tree.visit(transformer)
            file_path.write_text(modified.code)
            logger.info(f'Removed docstrings from {file_path}')
        except Exception as e:
            logger.error(f'Failed to process {file_path}: {str(e)}')

    yield
