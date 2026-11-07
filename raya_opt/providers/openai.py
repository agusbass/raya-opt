"""OpenAI Chat Completions adapter."""
from typing import List, Tuple
import requests

from .base import BaseProvider
from ..types import Message, Usage


class OpenAIProvider(BaseProvider):
    def complete(self, messages: List[Message], **kwargs) -> Tuple[str, Usage]:
        base = self.config.base_url or "https://api.openai.com/v1"
        url = f"{base}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **kwargs,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        r = requests.post(url, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        u = data.get("usage", {})
        usage = Usage(
            input_tokens=u.get("prompt_tokens", 0),
            output_tokens=u.get("completion_tokens", 0),
        )
        usage.cost_usd = self.estimate_cost(usage.input_tokens, usage.output_tokens)
        return content, usage
