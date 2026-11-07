"""M5: LLM Gateway.
- Provider abstraction
- Fallback chain (try providers in order; first success wins)
"""
import logging
from typing import Dict, List

from ..types import Message, ProviderConfig, Response, Usage
from ..providers.base import BaseProvider
from ..providers.openai import OpenAIProvider
from ..providers.anthropic import AnthropicProvider
from ..providers.ollama import OllamaProvider
from ..exceptions import AllProvidersFailed

log = logging.getLogger("raya_opt.m5")

PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


class Gateway:
    def __init__(self, providers: List[ProviderConfig], fallback_chain: List[str]):
        self.providers: Dict[str, BaseProvider] = {}
        for p in providers:
            if p.type not in PROVIDER_CLASSES:
                raise ValueError(f"unknown provider type: {p.type}")
            self.providers[p.name] = PROVIDER_CLASSES[p.type](p)
        self.chain = list(fallback_chain)
        for name in self.chain:
            if name not in self.providers:
                raise ValueError(f"fallback name {name!r} not in providers")

    def call(self, messages: List[Message], **kwargs) -> Response:
        errors = []
        tried: List[str] = []
        for name in self.chain:
            tried.append(name)
            provider = self.providers[name]
            try:
                content, usage = provider.complete(messages, **kwargs)
                return Response(
                    content=content,
                    provider=name,
                    model=provider.config.model,
                    usage=usage,
                    fallback_chain=tried,
                    retries=len(tried) - 1,
                )
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s failed: %s", name, e)
                errors.append(f"{name}: {e}")
                continue
        raise AllProvidersFailed("all providers failed: " + " | ".join(errors))
