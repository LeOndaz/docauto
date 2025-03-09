import logging

import pytest

from docugen.fs import FileSystemService


@pytest.fixture
def tmp_files(tmp_path):
    # Create test directory structure
    base = tmp_path / 'test_root'
    base.mkdir()

    # Valid files
    (base / 'test_file.txt').write_text('file content')
    (base / 'test.py').touch()

    # Directories
    (base / 'valid_dir').mkdir()
    (base / 'valid_dir' / 'dir_file.py').touch()
    (base / 'empty_dir').mkdir()

    # Invalid paths
    (base / 'invalid_file').touch()  # No extension
    return base


def test_read_file_success(file_system, tmp_files):
    test_file = tmp_files / 'test_file.txt'
    content = file_system.read_file(test_file)
    assert content == 'file content'


def test_read_file_failure(file_system, tmp_files, caplog):
    missing_file = tmp_files / 'missing.txt'
    with pytest.raises(FileNotFoundError):
        file_system.read_file(missing_file)
    assert 'Failed to read file' in caplog.text


def test_write_file_success(file_system, tmp_files):
    test_file = tmp_files / 'new_file.txt'
    file_system.write_file(test_file, 'new content')
    assert test_file.read_text() == 'new content'


def test_write_file_failure(file_system, tmp_files, caplog):
    # Test read-only file
    read_only = tmp_files / 'read_only.txt'
    read_only.touch(mode=0o444)
    with pytest.raises(PermissionError):
        file_system.write_file(read_only, 'content')
    assert 'Failed to write to file' in caplog.text


def test_find_python_files_success(file_system, tmp_files):
    result = list(file_system.find_python_files(tmp_files))
    expected = [
        tmp_files / 'test.py',
        tmp_files / 'valid_dir' / 'dir_file.py',
    ]
    assert sorted(result) == sorted(expected)


def test_find_python_files_non_directory(file_system, tmp_files, caplog):
    file_path = tmp_files / 'test_file.txt'
    result = list(file_system.find_python_files(file_path))
    assert len(result) == 0
    assert 'is not a directory' in caplog.text


def test_find_python_files_empty(file_system, tmp_files):
    empty_dir = tmp_files / 'empty_dir'
    result = list(file_system.find_python_files(empty_dir))
    assert len(result) == 0


def test_resolve_paths(file_system, tmp_files, caplog):
    input_paths = [
        str(tmp_files / 'valid_dir'),
        str(tmp_files / 'test.py'),
        str(tmp_files / 'missing'),
        str(tmp_files / 'invalid_file'),
    ]

    result = list(file_system.resolve_paths(input_paths))
    expected = [
        tmp_files / 'valid_dir' / 'dir_file.py',
        tmp_files / 'test.py',
    ]
    assert sorted(result) == sorted(expected)

    # Verify warnings
    logs = [rec.message for rec in caplog.records]
    assert 'Path does not exist' in logs[0]
    assert 'Skipping non-Python file' in logs[1]


def test_resolve_paths_edge_cases(file_system, tmp_files, caplog):
    # Test empty input
    assert list(file_system.resolve_paths([])) == []

    # Test non-existent directory
    result = list(file_system.resolve_paths([str(tmp_files / 'ghost_dir')]))
    assert len(result) == 0
    assert 'Path does not exist' in caplog.text


def test_logger_initialization():
    service = FileSystemService()
    assert service.logger.name == 'docugen'

    custom_logger = logging.getLogger('test')
    service = FileSystemService(logger=custom_logger)
    assert service.logger is custom_logger


def test_read_file_encoding_strict(file_system, tmp_files, caplog):
    # Create file with invalid UTF-8 bytes
    binary_file = tmp_files / 'binary.bin'
    binary_file.write_bytes(b'\x80abc')

    with pytest.raises(UnicodeDecodeError):
        file_system.read_file(binary_file)

    assert 'Failed to read file' in caplog.text
