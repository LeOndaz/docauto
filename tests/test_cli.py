import os
import tempfile
from pathlib import Path

import pytest

from docauto.cli import DocAutoCLI


def test_cli_initialization(cli, logger):
    """Test CLI initialization with logger"""
    assert isinstance(cli, DocAutoCLI)
    assert cli.logger == logger


def test_parser_creation(cli):
    """Test argument parser creation and default arguments"""

    # the cli needs an existing file to work
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_path = temp_file.name

        args = cli.parse_args([temp_path])

        assert not args['ollama']
        assert not args['openai']
        assert not args['dry_run']
        assert not args['verbose']
        assert args['paths'][0] == temp_path
        assert args['api_key'] is None
        assert args['base_url'] is None
        assert args['ai_model'] is None
        assert args['max_context'] is None
        assert args['constraints'] is None
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_cli_validation(cli):
    """Test configuration validation with presets"""
    # Test missing API key for OpenAI preset
    with pytest.raises(ValueError, match='API key required'):
        cli.resolve_config(
            {
                'openai': True,
                'ollama': False,
                'gemini': False,
                'deepseek': False,
                'base_url': 'https://api.openai.com/v1',
                'api_key': None,  # Not provided
                'ai_model': 'gpt-4',
                'max_context': None,
                'constraints': [],
                'paths': ['test.py'],
                'dry_run': False,
                'verbose': False,
                'overwrite': False,
            }
        )

    # Test invalid base URL format
    with pytest.raises(ValueError, match='Invalid base URL'):
        cli.resolve_config(
            {
                'ollama': True,
                'base_url': 'invalid-url',
                'api_key': 'ollama',
                'ai_model': None,
                'max_context': None,
                'constraints': [],
                'paths': ['test.py'],
                'dry_run': False,
                'verbose': False,
                'overwrite': False,
            }
        )


def test_preset_configuration(cli, preset_manager):
    """Test preset configuration handling"""
    args = {
        'ollama': True,
        'openai': False,
        'gemini': False,
        'deepseek': False,
        'base_url': None,
        'api_key': None,
        'ai_model': None,
        'max_context': None,
        'constraints': None,
        'paths': ['test.py'],
        'dry_run': False,
        'verbose': False,
        'overwrite': False,
    }

    ollama_preset = preset_manager.get_preset('ollama')
    config = cli.resolve_config(args)

    # Validate against expected preset values
    assert config.api.base_url == ollama_preset.api.base_url
    assert config.generation.ai_model == ollama_preset.generation.ai_model
    assert config.api.api_key == ollama_preset.api.api_key
    assert config.generation.max_context == ollama_preset.generation.max_context
    assert set(config.generation.constraints) == set(
        ollama_preset.generation.constraints
    )


def test_cli_argument_override(cli):
    """Test CLI argument overriding preset values"""
    custom_values = {
        'base_url': 'http://custom-url',
        'api_key': 'custom-key',
        'ai_model': 'custom-model',
        'max_context': 4096,
        'constraints': ['Custom constraint'],
    }

    args = {
        'ollama': True,
        'openai': False,
        'gemini': False,
        'deepseek': False,
        **custom_values,
        'paths': ['test.py'],
        'dry_run': False,
        'verbose': False,
        'overwrite': False,
    }

    config = cli.resolve_config(args)

    # Verify CLI values override preset values
    assert config.api.base_url == custom_values['base_url']
    assert config.api.api_key == custom_values['api_key']
    assert config.generation.ai_model == custom_values['ai_model']
    assert config.generation.max_context == custom_values['max_context']
    assert custom_values['constraints'][0] in config.generation.constraints


def test_file_processing(cli, file_system, files_for_testing, config):
    """Test file processing functionality"""

    for test_path in files_for_testing:
        # Use only the required arguments for ollama preset
        result = cli.run(['--ollama', str(test_path)])
        assert result == 0
        assert test_path in [Path(p) for p in file_system.reads]


def test_cli_error_handling(cli):
    """Test CLI error handling

    Argument parser exists with status code 2 for invalid inputs
    """

    # Test with invalid arguments
    result = cli.run(['--invalid-arg'])
    assert result == 1

    # Test with non-existent path
    result = cli.run(['non_existent_file.py', '--ollama'])
    assert result == 1
