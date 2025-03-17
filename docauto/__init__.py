from docauto.cli import DocAutoCLI
from docauto.config import APIConfig, DocAutoConfig, GenerationConfig
from docauto.config_parser import (
    BaseConfigParser,
    ConfigurationManager,
    YAMLConfigParser,
)
from docauto.exceptions import GenerationError, InvalidPythonModule
from docauto.generator import BaseDocsGenerator, DocAutoGenerator
from docauto.logger import _init_logger
from docauto.presets import DEEPSEEK_PRESET, GEMINI_PRESET, OLLAMA_PRESET, OPENAI_PRESET
from docauto.services import DocumentationService
from docauto.tracker import BaseProgressTracker, ProgressTracker, TrackedObjectState
from docauto.transformers import BaseDocTransformer, DocTransformer
from docauto.types import (
    APIOptions,
    DocAutoOptions,
    GenerationOptions,
    IgnorePattern,
    IgnorePatterns,
)

_init_logger()

__all__ = (
    # generators
    'BaseDocsGenerator',
    'DocAutoGenerator',
    # transformers
    'BaseDocTransformer',
    'DocTransformer',
    # docs
    'DocumentationService',
    # errors
    'InvalidPythonModule',
    'GenerationError',
    'DocAutoCLI',
    # parsers
    'BaseConfigParser',
    'YAMLConfigParser',
    'ConfigurationManager',
    # config
    'APIConfig',
    'GenerationConfig',
    'DocAutoConfig',
    # progress
    'BaseProgressTracker',
    'ProgressTracker',
    'TrackedObjectState',
    # presets
    'DEEPSEEK_PRESET',
    'GEMINI_PRESET',
    'OLLAMA_PRESET',
    'OPENAI_PRESET',
    # types
    'DocAutoOptions',
    'APIOptions',
    'GenerationOptions',
    'IgnorePattern',
    'IgnorePatterns',
)
