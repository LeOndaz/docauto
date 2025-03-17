# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.0.2

### Added

- Support for deepseek preset
- Codebase configuration files (.docauto.ya?ml/docauto.ya?ml) 
- Support for custom presets
- Scaffold for ignore patterns

### Changed

- Change the interface of all classes to match config.py models
- Change the config layout to use dataclasses, duplicated as TypedDict in types.py for convenience.
- Typehint all the codebase except cli.py
- Move the logger into a separate module

## 0.0.1

### Added

- Support for documenting codebases logically (function by function, class by class), sequentially.
- Initial support for CLI configuration `python -m docuauto.cli` with presets (ollama, gemini, openai)
- Support for basic progress tracking