from pathlib import Path

import pytest

from docugen.cli import DocuGenCLI


def test_cli_initialization(cli, logger):
    """Test CLI initialization with logger"""
    assert isinstance(cli, DocuGenCLI)
    assert cli.logger == logger


def test_parser_creation(cli):
    """Test argument parser creation and default arguments"""
    args = cli.parse_args(['test.py'])

    assert not args.ollama
    assert not args.openai
    assert not args.dry_run
    assert not args.verbose
    assert args.paths[0] == 'test.py'
    assert args.api_key is None
    assert args.base_url is None
    assert args.ai_model is None
    assert args.max_context is None
    assert args.constraints is None


def test_preset_configuration(cli, config):
    """Test preset configuration handling"""
    args = dict(
        ollama=True,
        openai=False,
        base_url=None,
        api_key=None,
        ai_model=None,
        max_context=None,
        paths=['test.py'],
        dry_run=False,
        verbose=False,
        constraints=config['constraints'],
    )

    merged_config = cli._merge_configuration(args)
    assert merged_config['base_url'] == config['base_url']
    assert merged_config['ai_model'] == config['ai_model']
    assert merged_config['api_key'] == config['api_key']
    assert merged_config['max_context'] == config['max_context']

    # Compare constraints as sets since order doesn't matter
    assert set(merged_config['constraints']) == set(config['constraints'])


def test_cli_argument_override(cli, config):
    """Test CLI argument overriding preset values"""
    custom_url = 'http://custom-url'
    custom_model = 'custom-model'
    custom_key = 'custom-key'
    custom_context = 4096
    custom_constraint = ['Custom constraint']

    args = dict(
        ollama=True,
        openai=False,
        base_url=custom_url,
        api_key=custom_key,
        ai_model=custom_model,
        max_context=custom_context,
        constraints=custom_constraint,
        paths=['test.py'],
        dry_run=False,
        verbose=False,
    )

    merged_config = cli._merge_configuration(args)
    assert merged_config['base_url'] == custom_url
    assert merged_config['ai_model'] == custom_model
    assert merged_config['api_key'] == custom_key
    assert merged_config['max_context'] == custom_context
    assert custom_constraint[0] in merged_config['constraints']


def test_cli_validation(cli):
    """Test configuration validation"""
    # Test missing base URL
    with pytest.raises(ValueError, match='Base URL is required'):
        cli._merge_configuration(
            dict(
                ollama=False,
                openai=False,
                base_url=None,
                api_key='key',
                ai_model='model',
                max_context=None,
                constraints=None,
                paths=['test.py'],
                dry_run=False,
                verbose=False,
            )
        )

    # Test missing API key for non-Ollama config
    with pytest.raises(ValueError, match='API key required'):
        cli._merge_configuration(
            dict(
                ollama=False,
                openai=True,
                base_url='http://test',
                api_key=None,
                ai_model='model',
                max_context=None,
                constraints=None,
                paths=['test.py'],
                dry_run=False,
                verbose=False,
            )
        )


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
