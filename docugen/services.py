import logging
from pathlib import Path
from typing import Optional, Union

import libcst as cst

from docugen.exceptions import InvalidPythonModule
from docugen.fs import FileSystemService
from docugen.generator import BaseDocsGenerator
from docugen.parsers import LLMDocstringResponseParser, LLMResponseParser
from docugen.tracker import BaseProgressTracker, ProgressTracker
from docugen.transformers import DocTransformer


class DocumentationService:
    """Service for processing files and generating documentation"""

    def __init__(
        self,
        generator: BaseDocsGenerator,
        fs_service: Optional[FileSystemService] = None,
        parser: Optional[LLMResponseParser] = None,
        progress_tracker: Optional[BaseProgressTracker] = None,
        transformer: Optional[DocTransformer] = None,
        overwrite: Optional[bool] = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.generator = generator
        self.parser = parser or LLMDocstringResponseParser()
        self.logger = logger or logging.getLogger('docugen')
        self.fs_service = fs_service or FileSystemService(self.logger)
        self.progress_tracker = progress_tracker or ProgressTracker(self.logger)
        self.transformer = transformer or DocTransformer(
            generator,
            parser,
            self.logger,
            overwrite=overwrite,
            progress_tracker=self.progress_tracker,
        )

    def parse_python(self, source):
        try:
            return cst.parse_module(source)
        except cst.ParserSyntaxError as e:
            self.logger.error(f'Failed to parse {e}')
            raise InvalidPythonModule(e)

    def process_file(self, file_path: Union[Path, str], plan: bool = False) -> bool:
        """Process a single Python file to add documentation

        Args:
            file_path: Path to the Python file
            plan: If True, only show change plan without writing

        Returns:
            True if changes were made, False otherwise
        """
        self.progress_tracker.track_file(str(file_path))

        try:
            # Reset transformer's processed objects
            self.transformer.processed_objects = []

            # Read file
            source = self.fs_service.read_file(file_path)
            module = self.parse_python(source)

            transformed_module = module.visit(self.transformer)
            modified_source = transformed_module.code

            # Check if changes were made
            if source != modified_source:
                if plan:
                    self.logger.info(f'[PLAN][UPDATE] {file_path}:')
                else:
                    self.fs_service.write_file(file_path, modified_source)
                    self.logger.info(f'[UPDATE] {file_path}')
                return True
            else:
                self.logger.info(f'No changes needed for {file_path}')
                return False

        except Exception as e:
            self.logger.error(f'Failed to process {file_path}: {str(e)}')
            return False
