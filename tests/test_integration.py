"""Integration tests for RayaOpt orchestrator with fake providers."""
import pytest

from raya_opt import RayaOpt, Config, ProviderConfig, Message
from raya_opt.matrices import m5_gateway
from raya_opt.types import Usage


class _Fake:
    """Provider stub matching BaseProvider interface."""
    def __init__(self, config, behavior="ok", cost=0.01):
        self.config = config
        self.behavior = behavior
        self.cost = cost

    def complete(self, messages, **kwargs):
        if self.behavior == "fail":
            raise RuntimeError("simulated")
        return "ok", Usage(input_tokens=10, output_tokens=5, cost_usd=self.cost)


@pytest.fixture
def fake_providers(monkeypatch):
    def make(behavior, cost):
        class _C(_Fake):
            def __init__(self, config):
                super().__init__(config, behavior=behavior, cost=cost)
        return _C

    monkeypatch.setattr(
        m5_gateway,
        "PROVIDER_CLASSES",
        {
            "cheap": make("ok", 0.001),
            "mid": make("ok", 0.01),
            "expensive_fail": make("fail", 0.10),
        },
    )


def _config(**overrides):
    base = dict(
        providers=[
            ProviderConfig(name="cheap_p", type="cheap", model="x"),
            ProviderConfig(name="mid_p", type="mid", model="y"),
        ],
        fallback_chain=["cheap_p", "mid_p"],
        budget_usd=0.10,
        max_depth=3,
        loop_window=3,
        loop_threshold=2,
    )
    base.update(overrides)
    return Config(**base)


def test_happy_path(fake_providers):
    client = RayaOpt(_config())
    r = client.complete([{"role": "user", "content": "hello"}])
    assert r.provider == "cheap_p"
    assert not r.blocked
    assert r.usage.cost_usd == pytest.approx(0.001)


def test_loop_blocks_request(fake_providers):
    client = RayaOpt(_config(loop_threshold=2))
    state = client.new_session()
    msgs = [{"role": "user", "content": "same"}]
    r1 = client.complete(msgs, state=state)
    assert not r1.blocked
    r2 = client.complete(msgs, state=state)
    assert r2.blocked
    assert "LoopDetected" in r2.block_reason


def test_budget_blocks(fake_providers):
    client = RayaOpt(_config(budget_usd=0.005))
    state = client.new_session()
    r1 = client.complete([{"role": "user", "content": "a"}], state=state)
    assert not r1.blocked
    # spent ~0.001, now force pre-spend close to cap
    state.spent_usd = 0.005
    r2 = client.complete([{"role": "user", "content": "b"}], state=state)
    assert r2.blocked
    assert "BudgetExceeded" in r2.block_reason


def test_fallback_chain_used(monkeypatch, fake_providers):
    cfg = Config(
        providers=[
            ProviderConfig(name="bad", type="expensive_fail", model="x"),
            ProviderConfig(name="good", type="cheap", model="y"),
        ],
        fallback_chain=["bad", "good"],
        budget_usd=0.10,
        max_depth=3,
        loop_window=3,
        loop_threshold=3,
    )
    client = RayaOpt(cfg)
    r = client.complete([{"role": "user", "content": "x"}])
    assert r.provider == "good"
    assert r.retries == 1
    assert r.fallback_chain == ["bad", "good"]
