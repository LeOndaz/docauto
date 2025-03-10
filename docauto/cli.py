import argparse
import logging
import signal
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, TypedDict

from docauto.config import (
    GEMINI_PRESET,
    OLLAMA_PRESET,
    OPENAI_PRESET,
    APIConfig,
    create_config,
)
from docauto.generator import DocAutoGenerator
from docauto.logger import SmartFormatter
from docauto.parsers import LLMDocstringResponseParser
from docauto.services import DocumentationService, FileSystemService


class CLIArgs(TypedDict, total=False):
    """Type-safe CLI arguments"""

    # presets
    ollama: bool
    openai: bool
    gemini: bool

    base_url: Optional[str]
    api_key: Optional[str]
    ai_model: Optional[str]
    max_context: Optional[int]
    constraints: Optional[List[str]]
    dry_run: bool
    verbose: bool
    paths: List[str]
    overwrite: bool


class BaseCLI(ABC):
    """Abstract base class for CLI implementations with customization support."""

    def __init__(
        self,
        fs_service: FileSystemService,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.fs_service = fs_service
        self.logger = logger or logging.getLogger('docauto')
        self.response_parser = LLMDocstringResponseParser(self.logger)
        self._setup_signal_handlers()
        self._shutdown_requested = False

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame) -> None:
        if self._shutdown_requested:
            self.logger.warning('Forcing shutdown...')
            sys.exit(1)
        self.logger.info('Graceful shutdown requested. Saving changes...')
        self._shutdown_requested = True

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    @abstractmethod
    def create_parser(self) -> argparse.ArgumentParser:
        pass

    def parse_args(self, args: Optional[List[str]] = None) -> CLIArgs:
        return self.create_parser().parse_args(args)

    @abstractmethod
    def run(self, args: Optional[List[str]] = None) -> int:
        pass


class PresetManager:
    """Registry and manager for preset configurations"""

    _presets: Dict[str, APIConfig] = {
        'ollama': OLLAMA_PRESET,
        'openai': OPENAI_PRESET,
        'gemini': GEMINI_PRESET,
    }

    @classmethod
    def get_preset(cls, name: str) -> APIConfig:
        if name not in cls._presets:
            raise ValueError(f'Unknown preset: {name}')
        return cls._presets[name]

    @classmethod
    def register_preset(cls, name: str, config: APIConfig) -> None:
        cls._presets[name] = config


class DocAutoCLI(BaseCLI):
    """CLI implementation with proper preset handling and constraint merging."""

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Generate Python documentation')
        preset_group = parser.add_mutually_exclusive_group()
        preset_group.add_argument(
            '--ollama', action='store_true', help='Use Ollama preset'
        )
        preset_group.add_argument(
            '--openai', action='store_true', help='Use OpenAI preset'
        )
        preset_group.add_argument(
            '--gemini', action='store_true', help='Use Gemini preset'
        )

        parser.add_argument('-b', '--base-url', help='API base URL')
        parser.add_argument('-k', '--api-key', help='API key for authentication')
        parser.add_argument('-m', '--model', dest='ai_model', help='AI model to use')
        parser.add_argument(
            '-mc', '--max-context', type=int, help='Maximum context size'
        )
        parser.add_argument(
            '-c',
            '--constraint',
            dest='constraints',
            action='append',
            help='Additional documentation constraints',
        )
        parser.add_argument(
            '-d',
            '--dry-run',
            action='store_true',
            help='Show changes without modifying files',
        )
        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            help='[Dangerous] Overwrite existing docstrings in codebase',
        )
        parser.add_argument(
            '-v', '--verbose', action='store_true', help='Enable verbose logging'
        )
        parser.add_argument('paths', nargs='+', help='Files/directories to process')
        return parser

    def _configure_logging(self, verbose: bool) -> None:
        level = logging.DEBUG if verbose else logging.WARNING
        handler = logging.StreamHandler()
        formatter = SmartFormatter(
            default_format='[%(levelname)s] [%(asctime)s] [%(name)s]: %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.setLevel(level)
        self.logger.addHandler(handler)

    def _merge_configuration(self, args: CLIArgs) -> APIConfig:
        """Merge CLI arguments with preset configuration"""
        preset = None
        config = {}

        # Use dict.get() for safe access since TypedDict doesn't validate at runtime
        if args.get('ollama'):
            preset = PresetManager.get_preset('ollama')
        elif args.get('openai'):
            preset = PresetManager.get_preset('openai')
        elif args.get('gemini'):
            preset = PresetManager.get_preset('gemini')
        else:
            self.logger.info('not using a predefined preset.')

        # Replace with preset values if available
        if preset:
            config = preset

        # Override preset values with CLI arguments if provided
        config_args = {
            'base_url': args.get('base_url') or config.get('base_url'),
            'ai_model': args.get('ai_model') or config.get('ai_model'),
            'api_key': args.get('api_key') or config.get('api_key'),
            'max_context': args.get('max_context') or config.get('max_context'),
            'constraints': args.get('constraints') or config.get('constraints'),
        }

        config = create_config(**config_args)

        # Validate final configuration
        if not config['base_url']:
            raise ValueError('Base URL is required. Use a preset or provide --base-url')
        if not config['ai_model']:
            raise ValueError('AI model is required. Use a preset or provide --model')
        if not config['api_key'] and 'localhost' not in config['base_url']:
            raise ValueError('API key required for non-local configurations')

        return config

    def _process_files(
        self,
        docs_service: DocumentationService,
        paths: List[str],
        dry_run: bool,
    ) -> tuple[int, int]:
        """Process files and return counts."""
        file_count = 0
        updated_count = 0
        resolved_paths = list(self.fs_service.resolve_paths(paths))

        if not resolved_paths:
            raise ValueError('No valid files found to process')

        for file_path in resolved_paths:
            if self.shutdown_requested:
                break
            file_count += 1
            if docs_service.process_file(file_path, dry_run):
                updated_count += 1
        return file_count, updated_count

    def run(self, args: Optional[List[str]] = None) -> int:
        try:
            parsed_args = self.parse_args(args)
            cli_args = CLIArgs(
                ollama=parsed_args.ollama,
                openai=parsed_args.openai,
                gemini=parsed_args.gemini,
                base_url=parsed_args.base_url,
                api_key=parsed_args.api_key,
                ai_model=parsed_args.ai_model,
                max_context=parsed_args.max_context,
                constraints=parsed_args.constraints,
                dry_run=parsed_args.dry_run,
                verbose=parsed_args.verbose,
                paths=parsed_args.paths,
                overwrite=parsed_args.overwrite,
            )
            self._configure_logging(cli_args['verbose'])

            config = self._merge_configuration(cli_args)
            doc_service = DocumentationService(
                DocAutoGenerator(
                    base_url=config['base_url'],
                    ai_model=config['ai_model'],
                    api_key=config['api_key'],
                    max_context=config['max_context'],
                    constraints=config['constraints'],
                    logger=self.logger,
                ),
                overwrite=cli_args['overwrite'],
                fs_service=self.fs_service,
                parser=self.response_parser,
                logger=self.logger,
            )

            file_count, updated_count = self._process_files(
                doc_service,
                parsed_args.paths,
                parsed_args.dry_run,
            )

            result_msg = (
                f'Dry run: {updated_count}/{file_count} files would update'
                if parsed_args.dry_run
                else f'Processed: {updated_count}/{file_count} files updated'
            )
            self.logger.info(result_msg)
            return 0

        except SystemExit as e:
            self.logger.error(
                f'Invalid arguments: {str(e)}',
                exc_info=True,
            )
            return 1
        except Exception as e:
            self.logger.error(
                f'Operation failed: {str(e)}',
                exc_info=parsed_args.verbose,
            )
            return 1


def main() -> int:
    file_system = FileSystemService()
    return DocAutoCLI(file_system).run()


if __name__ == '__main__':
    sys.exit(main())
