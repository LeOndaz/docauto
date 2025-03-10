# DocAuto

A tool for generating documentation from code using LLMs.

## CLI Usage

DocAuto provides a command-line interface for generating documentation from your code. The CLI is implemented in `cli.py` and offers several commands and options.

### Basic Usage

```bash
python -m docauto [paths...] [options]
```

### Preset Configurations

DocAuto provides preset configurations for popular LLM services:

#### Ollama Preset
```bash
python -m docauto --ollama [paths...]
```
Uses the following configuration:
- Base URL: http://localhost:11434/v1
- Model: phi4
- Max Context: 16384

#### OpenAI Preset
```bash
python -m docauto --openai -k your_api_key [paths...]
```
Uses the following configuration:
- Base URL: https://api.openai.com/v1
- Model: gpt-4o-mini
- Max Context: 16384
- Requires API key

#### Gemini Preset
```bash
python -m docauto --gemini -k your_api_key [paths...]
```
Uses the following configuration:
- Base URL: https://generativelanguage.googleapis.com/v1beta/openai/
- Model: gemini-2.0-flash-exp
- Max Context: 131072
- Requires API key

### Options

#### API Configuration
- `-b, --base-url`: API base URL for the LLM service
- `-k, --api-key`: API key for authentication
- `-m, --model`: AI model to use
- `-mc, --max-context`: Maximum context size
- `-c, --constraint`: Add a documentation constraint (can be used multiple times)
- `-d, --dry-run`: Show changes without modifying files
- `-v, --verbose`: Enable verbose logging
- `-o, --overwrite`: [Dangerous] Overwrite existing docstrings in codebase
- `paths`: One or more Python files or directories to process

### Examples

```bash
# Process a single file
python -m docauto example.py

# Process multiple files with API key
python -m docauto file1.py file2.py -k your_api_key

# Process a directory in dry-run mode
python -m docauto ./src -d

# Process with custom model and verbose logging
python -m docauto ./src -m gpt-4 -v

# Use Ollama preset for local processing
python -m docauto ./src --ollama

# Use OpenAI preset with API key
python -m docauto ./src --openai -k your_api_key
```

The tool will process the specified Python files, generate documentation using the configured LLM, and update the files with the generated documentation. Use the `--dry-run` option to preview changes without modifying files.
