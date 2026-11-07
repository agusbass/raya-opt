"""3 PoC scenarios:
  1. cost_saving      — baseline vs Raya-Opt chain
  2. loop_protection  — agent loop bug, with/without M1
  3. uptime           — fallback under provider outage
"""
import time
from dataclasses import dataclass, asdict
from typing import List, Optional

from raya_opt import RayaOpt
from raya_opt.types import Message
from .prompts import Prompt


@dataclass
class ResultRow:
    scenario: str
    run: str               # e.g. "baseline" / "optimized"
    prompt_id: str
    category: str
    provider: str
    model: str
    retries: int
    fallback_chain: str    # joined with '>'
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    blocked: bool
    block_reason: Optional[str]
    response_excerpt: str  # first 80 chars

    def to_dict(self):
        return asdict(self)


def _excerpt(text: str, n: int = 80) -> str:
    s = (text or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "..."


def _call_once(client: RayaOpt, scenario: str, run: str, prompt: Prompt, state=None) -> ResultRow:
    t0 = time.perf_counter()
    resp = client.complete(
        [Message(role="user", content=prompt.text)],
        state=state,
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return ResultRow(
        scenario=scenario,
        run=run,
        prompt_id=prompt.id,
        category=prompt.category,
        provider=resp.provider,
        model=resp.model,
        retries=resp.retries,
        fallback_chain=">".join(resp.fallback_chain),
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        cost_usd=round(resp.usage.cost_usd, 6),
        latency_ms=round(latency_ms, 2),
        blocked=resp.blocked,
        block_reason=resp.block_reason,
        response_excerpt=_excerpt(resp.content),
    )


# ── Scenario 1 ──────────────────────────────────────────────────
def run_cost_saving(
    baseline_client: RayaOpt,
    optimized_client: RayaOpt,
    prompts: List[Prompt],
) -> List[ResultRow]:
    rows: List[ResultRow] = []
    for p in prompts:
        rows.append(_call_once(baseline_client, "cost_saving", "baseline", p))
        rows.append(_call_once(optimized_client, "cost_saving", "optimized", p))
    return rows


# ── Scenario 2 ──────────────────────────────────────────────────
def run_loop_protection(
    no_breaker_client: RayaOpt,
    with_breaker_client: RayaOpt,
    repeats: int = 20,
) -> List[ResultRow]:
    """Simulate an agent stuck in a loop firing identical prompts."""
    rows: List[ResultRow] = []
    loop_prompt = Prompt(
        id="loop_x",
        category="agent_loop",
        text="Cari info tentang X, verifikasi, ulangi sampai yakin.",
    )

    # without breaker: every call goes through (loop_threshold huge)
    state_a = no_breaker_client.new_session()
    for i in range(repeats):
        r = _call_once(no_breaker_client, "loop_protection", "no_breaker", loop_prompt, state=state_a)
        r.prompt_id = f"loop_x_{i+1:02d}"
        rows.append(r)
        if r.blocked:
            break

    # with breaker: should block at 3rd identical call
    state_b = with_breaker_client.new_session()
    for i in range(repeats):
        r = _call_once(with_breaker_client, "loop_protection", "with_breaker", loop_prompt, state=state_b)
        r.prompt_id = f"loop_x_{i+1:02d}"
        rows.append(r)
        if r.blocked:
            break

    return rows


# ── Scenario 3 ──────────────────────────────────────────────────
def run_uptime(
    client_with_broken_first: RayaOpt,
    prompts: List[Prompt],
) -> List[ResultRow]:
    """First provider always fails; verify 100% requests served via fallback."""
    rows: List[ResultRow] = []
    for p in prompts:
        rows.append(_call_once(client_with_broken_first, "uptime", "fallback_test", p))
    return rows
