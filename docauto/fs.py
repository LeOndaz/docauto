import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, List, Optional


class BaseFileSystem(ABC):
    """Abstract interface for file system operations"""

    @abstractmethod
    def read_file(self, path: Path) -> str:
        """Read file content"""
        pass

    @abstractmethod
    def write_file(self, path: Path, content: str) -> None:
        """Write content to file"""
        pass

    @abstractmethod
    def find_python_files(self, directory: Path) -> Iterator[Path]:
        """Find all Python files in a directory recursively"""
        pass

    @abstractmethod
    def resolve_paths(self, paths: List[str]) -> Iterator[Path]:
        """Resolve a list of paths to Python files"""
        pass


class FileSystemService(BaseFileSystem):
    """Service for file system operations with easier testing support"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('docauto')

    def read_file(self, path: Path) -> str:
        """Read file content"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f'Failed to read file {path}: {str(e)}')
            raise

    def write_file(self, path: Path, content: str) -> None:
        """Write content to file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f'Failed to write to file {path}: {str(e)}')
            raise

    def find_python_files(self, directory: Path) -> Iterator[Path]:
        """Find all Python files in a directory recursively"""
        if not directory.is_dir():
            self.logger.warning(f'{directory} is not a directory')
            return

        try:
            yield from directory.rglob('*.py')
        except Exception as e:
            self.logger.error(f'Error searching directory {directory}: {str(e)}')
            raise

    def resolve_paths(self, paths: List[str]) -> Iterator[Path]:
        """Resolve a list of paths to Python files"""
        for path_str in paths:
            path = Path(path_str)

            if not path.exists():
                self.logger.warning(f'Path does not exist: {path}')
                continue

            if path.is_dir():
                yield from self.find_python_files(path)
            elif path.is_file() and path.suffix == '.py':
                yield path
            else:
                self.logger.warning(f'Skipping non-Python file: {path}')
