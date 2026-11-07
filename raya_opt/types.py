"""Core data types for Raya-Opt."""
from dataclasses import dataclass, field
from typing import List, Optional, Literal


@dataclass
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class ProviderConfig:
    name: str
    type: Literal["openai", "anthropic", "ollama"]
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class Response:
    content: str
    provider: str
    model: str
    usage: Usage
    fallback_chain: List[str] = field(default_factory=list)
    retries: int = 0
    blocked: bool = False
    block_reason: Optional[str] = None
