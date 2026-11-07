"""Tests for M5 gateway — uses fake providers (no network)."""
import pytest

from raya_opt.types import Message, ProviderConfig, Usage
from raya_opt.matrices import m5_gateway
from raya_opt.matrices.m5_gateway import Gateway
from raya_opt.exceptions import AllProvidersFailed


class FakeProvider:
    def __init__(self, config, behavior="ok"):
        self.config = config
        self.behavior = behavior
        self.calls = 0

    def complete(self, messages, **kwargs):
        self.calls += 1
        if self.behavior == "fail":
            raise RuntimeError(f"{self.config.name} simulated fail")
        return f"hello from {self.config.name}", Usage(
            input_tokens=5, output_tokens=3, cost_usd=0.001
        )


def _patched_gateway(monkeypatch, behaviors):
    """Build a Gateway where each provider type maps to a FakeProvider with given behavior."""

    def make_class(behavior):
        class _C(FakeProvider):
            def __init__(self, config):
                super().__init__(config, behavior=behavior)
        return _C

    monkeypatch.setattr(
        m5_gateway,
        "PROVIDER_CLASSES",
        {f"t{i}": make_class(b) for i, b in enumerate(behaviors)},
    )
    providers = [
        ProviderConfig(name=f"p{i}", type=f"t{i}", model="m") for i in range(len(behaviors))
    ]
    chain = [f"p{i}" for i in range(len(behaviors))]
    return Gateway(providers, chain)


def test_first_provider_succeeds(monkeypatch):
    g = _patched_gateway(monkeypatch, ["ok", "ok"])
    r = g.call([Message(role="user", content="hi")])
    assert r.provider == "p0"
    assert r.retries == 0
    assert r.fallback_chain == ["p0"]


def test_fallback_on_failure(monkeypatch):
    g = _patched_gateway(monkeypatch, ["fail", "ok"])
    r = g.call([Message(role="user", content="hi")])
    assert r.provider == "p1"
    assert r.retries == 1
    assert r.fallback_chain == ["p0", "p1"]


def test_all_fail(monkeypatch):
    g = _patched_gateway(monkeypatch, ["fail", "fail"])
    with pytest.raises(AllProvidersFailed):
        g.call([Message(role="user", content="hi")])


def test_unknown_fallback_name_raises():
    p = ProviderConfig(name="known", type="openai", model="x", api_key="k")
    with pytest.raises(ValueError):
        Gateway([p], fallback_chain=["unknown"])
