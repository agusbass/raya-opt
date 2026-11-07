"""Mock providers for PoC dry-run.

Simulates realistic latency + cost. Lets you exercise the full PoC pipeline
without burning API credits.
"""
import time
import random
import hashlib
from typing import List, Tuple

from raya_opt.providers.base import BaseProvider
from raya_opt.types import Message, Usage


# fake cost & latency profiles
PROFILES = {
    "mock_llama":  {"latency_ms": (80,  200),  "ipm": 0.0,     "opm": 0.0,     "fail_rate": 0.0},
    "mock_gpt4mini": {"latency_ms": (400, 1200), "ipm": 0.00015, "opm": 0.00060, "fail_rate": 0.0},
    "mock_haiku":  {"latency_ms": (300, 900),  "ipm": 0.001,   "opm": 0.005,   "fail_rate": 0.0},
    "mock_premium":{"latency_ms": (700, 1800), "ipm": 0.003,   "opm": 0.015,   "fail_rate": 0.0},
    "mock_broken": {"latency_ms": (50,  100),  "ipm": 0.0,     "opm": 0.0,     "fail_rate": 1.0},
    # For testing fallback under partial failures, use mock_flaky:
    "mock_flaky":  {"latency_ms": (200, 600),  "ipm": 0.0001,  "opm": 0.0004,  "fail_rate": 0.3},
}


def _fake_tokenize(text: str) -> int:
    """Rough token count: 1 token per ~4 chars."""
    return max(1, len(text) // 4)


def _fake_response(prompt_text: str) -> str:
    """Generate a deterministic-ish fake response of plausible length."""
    seed = int(hashlib.md5(prompt_text.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    n_words = rng.randint(8, 60)
    words = [f"w{rng.randint(0, 999)}" for _ in range(n_words)]
    return " ".join(words) + "."


class MockProvider(BaseProvider):
    """Drop-in mock matching BaseProvider. Type = mock_<profile>."""

    def complete(self, messages: List[Message], **kwargs) -> Tuple[str, Usage]:
        profile_name = self.config.type
        if profile_name not in PROFILES:
            raise ValueError(f"unknown mock profile: {profile_name}")
        prof = PROFILES[profile_name]

        # simulate latency
        lo, hi = prof["latency_ms"]
        time.sleep(random.uniform(lo, hi) / 1000.0)

        # simulate failure
        if random.random() < prof["fail_rate"]:
            raise RuntimeError(f"{profile_name} simulated transient failure")

        prompt_text = "\n".join(m.content for m in messages)
        content = _fake_response(prompt_text)

        in_toks = _fake_tokenize(prompt_text)
        out_toks = _fake_tokenize(content)
        cost = in_toks / 1000.0 * prof["ipm"] + out_toks / 1000.0 * prof["opm"]

        return content, Usage(
            input_tokens=in_toks,
            output_tokens=out_toks,
            cost_usd=cost,
        )


def register_mocks():
    """Inject mock provider classes into the gateway registry."""
    from raya_opt.matrices import m5_gateway

    m5_gateway.PROVIDER_CLASSES.update({
        "mock_llama":   MockProvider,
        "mock_gpt4mini": MockProvider,
        "mock_haiku":   MockProvider,
        "mock_premium": MockProvider,
        "mock_broken":  MockProvider,
        "mock_flaky":   MockProvider,
    })
