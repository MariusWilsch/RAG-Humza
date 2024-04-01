from dataclasses import dataclass
import yaml


@dataclass
class ClaudeConfig:
    CLAUDE_MODEL_OPUS: str
    CLAUDE_MODEL_SONNET: str
    CLAUDE_SYSTEM_PROMPT: str
    CLAUDE_SYSTEM_PROMPT_CSV: str


@dataclass
class OpenAIConfig:
    SYSTEM_PROMPT_FAV: str
    SYSTEM_PROMPT_LAW: str
    SYSTEM_PROMPT_NEURO: str
    CHAT_MODEL: str
    EMBEDDING_MODEL: str
    SYSTEM_PROMPT_CONSULT: str


@dataclass
class ChromaConfig:
    K_RESULTS: int


@dataclass
class ExtrasConfig:
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int


@dataclass
class AppConfig:
    CLAUDE_CONFIG: ClaudeConfig
    OPENAI: OpenAIConfig
    CHROMA: ChromaConfig
    EXTRAS: ExtrasConfig


def load_config(file_path: str = "config/config.yml") -> AppConfig:
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    return AppConfig(
        CLAUDE_CONFIG=ClaudeConfig(**data["CLAUDE_CONFIG"]),
        OPENAI=OpenAIConfig(**data["OPENAI"]),
        CHROMA=ChromaConfig(**data["CHROMA"]),
        EXTRAS=ExtrasConfig(**data["EXTRAS"]),
    )
