import argparse
import logging
import signal
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

import openai

from docauto.config import DocAutoConfig
from docauto.generator import DocAutoGenerator
from docauto.parsers import LLMDocstringResponseParser
from docauto.presets import PresetManager
from docauto.services import DocumentationService, FileSystemService


# TypedDict configurations for CLI args
class BaseConfig(TypedDict):
    paths: List[str]
    dry_run: bool
    verbose: bool
    overwrite: bool
    base_url: str
    api_key: str


class OllamaConfig(BaseConfig):
    ollama: Literal[True]
    api_key: Literal['ollama']


class OpenAIConfig(BaseConfig):
    openai: Literal[True]


class GeminiConfig(BaseConfig):
    gemini: Literal[True]


class DeepSeekConfig(BaseConfig):
    deepseek: Literal[True]


CLIArgs = Union[
    OllamaConfig,
    OpenAIConfig,
    GeminiConfig,
    DeepSeekConfig,
]


@dataclass(frozen=True)
class DocAutoCLIConfig(DocAutoConfig):
    """Extended configuration incorporating CLI-specific settings"""

    paths: List[str]

    overwrite: bool = False
    dry_run: bool = False
    verbose: bool = False
    ollama: bool = False
    openai: bool = False
    gemini: bool = False
    deepseek: bool = False


class BaseCLI(ABC):
    """Abstract base class for CLI implementations"""

    def __init__(
        self,
        fs_service: FileSystemService,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.fs_service = fs_service
        self.logger = logger or logging.getLogger('docauto')
        self.response_parser = LLMDocstringResponseParser(self.logger)
        self._shutdown_requested = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame) -> None:
        if self._shutdown_requested:
            self.logger.warning('Forcing shutdown...')
            sys.exit(1)
        self.logger.info('Graceful shutdown requested...')
        self._shutdown_requested = True

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested

    @abstractmethod
    def create_parser(self) -> argparse.ArgumentParser:
        pass

    def validate_args(self, args: Dict[str, Any] | None) -> None:
        """Validate args after parsing"""

    def parse_args(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        args = vars(self.create_parser().parse_args(args))
        self.validate_args(args)
        return args

    @abstractmethod
    def run(self, args: Optional[List[str]] = None) -> int:
        pass


class DocAutoCLI(BaseCLI):
    """CLI implementation with unified configuration handling"""

    presets = ['ollama', 'openai', 'gemini', 'deepseek']

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description='AI-powered docstring generation',
        )

        def on_error(message):
            raise argparse.ArgumentTypeError(message)

        parser.error = on_error

        preset_group = parser.add_mutually_exclusive_group(required=False)
        preset_group.add_argument(
            '--ollama', action='store_true', help='Use Ollama preset'
        )
        preset_group.add_argument(
            '--openai', action='store_true', help='Use OpenAI preset'
        )
        preset_group.add_argument(
            '--gemini', action='store_true', help='Use Gemini preset'
        )
        preset_group.add_argument(
            '--deepseek', action='store_true', help='Use Deepseek preset'
        )

        parser.add_argument('-b', '--base-url', help='Custom API base URL')
        parser.add_argument('-k', '--api-key', help='API authentication key')
        parser.add_argument(
            '-m', '--model', dest='ai_model', help='Model to use for generation'
        )
        parser.add_argument(
            '-mc', '--max-context', type=int, help='Max context window size'
        )
        parser.add_argument(
            '-c',
            '--constraint',
            dest='constraints',
            action='append',
            help='Documentation constraints',
        )
        parser.add_argument(
            '-d',
            '--dry-run',
            action='store_true',
            help='Simulate changes without writing',
        )
        parser.add_argument(
            '-o',
            '--overwrite',
            action='store_true',
            help='Overwrite existing docstrings',
        )
        parser.add_argument(
            '-v', '--verbose', action='store_true', help='Enable verbose output'
        )
        parser.add_argument('paths', nargs='+', help='Files/directories to process')
        return parser

    def validate_args(self, args: Dict[str, Any]) -> None:
        paths = args['paths']

        if not self.fs_service.is_valid_paths(paths):
            raise ValueError('Invalid path provided')

    def resolve_config(self, args: Dict[str, Any]) -> DocAutoCLIConfig:
        """Resolve and validate unified configuration from CLI args and presets"""
        preset_name = self._get_active_preset(args)

        if preset_name:
            preset = PresetManager.get_preset(preset_name)

        # Merge preset with CLI arguments
        merged_api = {
            'base_url': args.get('base_url') or preset.api.base_url if preset else None,
            'api_key': args.get('api_key') or preset.api.api_key if preset else None,
        }

        merged_generation = {
            'ai_model': args.get('ai_model') or preset.generation.ai_model
            if preset
            else None,
            'max_context': args.get('max_context') or preset.generation.max_context
            if preset
            else None,
            'constraints': args.get('constraints') or preset.generation.constraints
            if preset
            else None,
        }

        base_config = DocAutoConfig.create(
            api=merged_api,
            generation=merged_generation,
        )
        # Create extended CLI configuration
        return DocAutoCLIConfig(
            api=base_config.api,
            generation=base_config.generation,
            overwrite=args['overwrite'],
            dry_run=args['dry_run'],
            paths=args['paths'],
            verbose=args['verbose'],
        )

    def _get_active_preset(self, args: Dict[str, Any]) -> str:
        """Identify which preset is being used"""
        for preset in self.presets:
            if args.get(preset):
                return preset
        return None

    def configure_logging(self, verbose: bool) -> None:
        """Set up logging infrastructure"""
        level = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def _process_files(
        self,
        service: DocumentationService,
        paths: List[str],
        dry_run: bool,
    ) -> tuple[int, int]:
        """Execute documentation processing workflow"""
        processed = updated = 0
        for path in self.fs_service.resolve_paths(paths):
            if self.shutdown_requested:
                break
            processed += 1
            if service.process_file(path, dry_run):
                updated += 1
        return processed, updated

    def run(self, args: Optional[List[str]] = None) -> int:
        try:
            raw_args = self.parse_args(args)
            config = self.resolve_config(raw_args)
            self.configure_logging(raw_args['verbose'])

            # Initialize service components
            client = openai.Client(
                api_key=config.api.api_key,
                base_url=config.api.base_url,
            )

            generator = DocAutoGenerator(
                client=client,
                ai_model=config.generation.ai_model,
                max_context=config.generation.max_context,
                constraints=config.generation.constraints,
                logger=self.logger,
            )

            doc_service = DocumentationService(
                generator=generator,
                overwrite=config.overwrite,
                fs_service=self.fs_service,
                parser=self.response_parser,
                logger=self.logger,
            )

            # Execute processing pipeline
            total, updated = self._process_files(
                doc_service,
                raw_args['paths'],
                config.dry_run,
            )

            self.logger.info(
                f'Processed {total} files ({updated} updated)'
                + (' [dry-run]' if config.dry_run else '')
            )
            return 0

        except Exception as e:
            self.logger.exception(f'Operation failed: {str(e)}')
            return 1


def main() -> int:
    return DocAutoCLI(FileSystemService()).run()


if __name__ == '__main__':
    sys.exit(main())
