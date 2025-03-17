from typing import Dict

from docauto.config import DocAutoConfig
from docauto.types import DocAutoOptions

__all__ = ('OLLAMA_PRESET', 'OPENAI_PRESET', 'GEMINI_PRESET', 'DEEPSEEK_PRESET')

OLLAMA_PRESET = {
    'api': {
        'base_url': 'http://localhost:11434/v1',
        'api_key': 'ollama',
    },
    'generation': {
        'ai_model': 'phi4',
        'max_context': 16384,
    },
}

OPENAI_PRESET = {
    'api': {
        'base_url': 'https://api.openai.com/v1',
        'api_key': None,  # API key will still be validated later
    },
    'generation': {
        'ai_model': 'gpt-4o-mini',
        'max_context': 16384,
    },
}

GEMINI_PRESET = {
    'api': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'api_key': None,
    },
    'generation': {
        'ai_model': 'gemini-2.0-flash-exp',  # this is a free API
        'max_context': 131_072,
    },
}

DEEPSEEK_PRESET = {
    'api': {
        'base_url': 'https://api.deepseek.com/v1',
        'api_key': None,
    },
    'generation': {
        'ai_model': 'deepseek-chat',
        'max_context': 65_536,
    },
}


class PresetManager:
    """Registry and manager for preset configurations"""

    _presets: Dict[str, DocAutoOptions] = {
        'ollama': OLLAMA_PRESET,
        'openai': OPENAI_PRESET,
        'gemini': GEMINI_PRESET,
        'deepseek': DEEPSEEK_PRESET,
    }

    @classmethod
    def get_preset(cls, name: str) -> DocAutoConfig:
        if name not in cls._presets:
            raise ValueError(f'Unknown preset: {name}')
        return DocAutoConfig.create(**cls._presets[name])

    @classmethod
    def register_preset(cls, name: str, config: dict) -> None:
        if name in cls._presets:
            raise ValueError(f'Preset {name} already exists')

        cls._presets[name] = config
