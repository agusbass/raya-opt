"""Ollama (local) adapter — Llama 3, Mistral, etc."""
from typing import List, Tuple
import requests

from .base import BaseProvider
from ..types import Message, Usage


class OllamaProvider(BaseProvider):
    def complete(self, messages: List[Message], **kwargs) -> Tuple[str, Usage]:
        base = self.config.base_url or "http://localhost:11434"
        url = f"{base}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        options = kwargs.pop("options", None)
        if options:
            payload["options"] = options

        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        content = data["message"]["content"]
        usage = Usage(
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
        )
        usage.cost_usd = self.estimate_cost(usage.input_tokens, usage.output_tokens)
        return content, usage
