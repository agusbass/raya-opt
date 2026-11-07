"""Anthropic Messages API adapter."""
from typing import List, Tuple
import requests

from .base import BaseProvider
from ..types import Message, Usage


class AnthropicProvider(BaseProvider):
    def complete(self, messages: List[Message], **kwargs) -> Tuple[str, Usage]:
        base = self.config.base_url or "https://api.anthropic.com/v1"
        url = f"{base}/messages"

        system_text = None
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_text = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        payload = {
            "model": self.config.model,
            "messages": chat_msgs,
            "max_tokens": kwargs.pop("max_tokens", 1024),
            **kwargs,
        }
        if system_text:
            payload["system"] = system_text

        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        r = requests.post(url, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        content = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        u = data.get("usage", {})
        usage = Usage(
            input_tokens=u.get("input_tokens", 0),
            output_tokens=u.get("output_tokens", 0),
        )
        usage.cost_usd = self.estimate_cost(usage.input_tokens, usage.output_tokens)
        return content, usage
