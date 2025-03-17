from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import yaml

from docauto.config import DocAutoConfig


class BaseConfigParser(ABC):
    """Abstract base class for configuration parsers."""

    config_class = DocAutoConfig

    @abstractmethod
    def can_handle(self, file_path: Union[str, Path]) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file_path: Path to the configuration file

        Returns:
            bool: True if this parser can handle the file, False otherwise
        """
        pass

    @abstractmethod
    def parse(self, file_path: Union[str, Path]) -> DocAutoConfig:
        """Parse the configuration file and return the configuration dictionary.

        Args:
            file_path: Path to the configuration file

        Returns:
            DocAutoConfig: Parsed configuration object

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid
        """
        pass


class YAMLConfigParser(BaseConfigParser):
    """YAML configuration parser implementation."""

    def can_handle(self, file_path: Union[str, Path]) -> bool:
        file_path = Path(file_path)
        return file_path.suffix.lower() in ['.yml', '.yaml']

    def parse(self, file_path: Union[str, Path]) -> DocAutoConfig:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f'Configuration file not found: {file_path}')

        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}

            api_config = config_data.get('api', {})
            generation_config = config_data.get('generation', {})
            return self.config_class.create(
                api=api_config, generation=generation_config
            )
        except yaml.YAMLError as e:
            raise ValueError(f'Invalid YAML configuration: {e}')


class ConfigurationManager:
    """Manages configuration parsing and loading."""

    def __init__(self):
        self.parsers: List[BaseConfigParser] = [YAMLConfigParser()]
        self.default_files = [
            '.docauto.yml',
            '.docauto.yaml',
            'docauto.yml',
            'docauto.yaml',
        ]

    def register_parser(self, parser: BaseConfigParser) -> None:
        """Register a new configuration parser.

        Args:
            parser: Configuration parser instance
        """
        self.parsers.append(parser)

    def load_config(
        self, file_path: Optional[Union[str, Path]] = None
    ) -> DocAutoConfig:
        """Load configuration from file.

        Args:
            file_path: Path to the configuration file. If None, searches for default files.

        Returns:
            Config: Parsed configuration dictionary

        Raises:
            FileNotFoundError: If no configuration file is found
            ValueError: If no parser can handle the file or if the file is invalid
        """
        config_path = self._find_config_file(file_path)
        if not config_path:
            raise FileNotFoundError(
                f'No configuration files found, supported files are: {", ".join(self.default_files)}'
            )

        for parser in self.parsers:
            if parser.can_handle(config_path):
                return parser.parse(config_path)

        raise ValueError(f'No parser found for file: {config_path}')

    def _find_config_file(
        self, file_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """Find the configuration file.

        Args:
            file_path: Explicit path to configuration file

        Returns:
            Optional[Path]: Path to the configuration file if found, None otherwise
        """
        if file_path:
            path = Path(file_path)
            return path if path.exists() else None

        # Search for default configuration files
        for default_file in self.default_files:
            path = Path(default_file)
            if path.exists():
                return path

        return None
