"""Raya-Opt orchestrator (the '0' node in the 0-n-0 topology).

Pipeline per request:
    0 → M1 pre-checks → M5 call → M1 record → 0
"""
import logging
from typing import Dict, List, Optional, Union

from .config import Config
from .types import Message, Response, Usage
from .matrices.m1_breaker import CircuitBreaker, BreakerState
from .matrices.m5_gateway import Gateway
from .exceptions import (
    LoopDetected,
    BudgetExceeded,
    MaxDepthExceeded,
    AllProvidersFailed,
)

log = logging.getLogger("raya_opt")


class RayaOpt:
    """Entry & exit point for all LLM calls."""

    def __init__(self, config: Config):
        self.config = config
        self.breaker = CircuitBreaker(
            budget_usd=config.budget_usd,
            max_depth=config.max_depth,
            loop_window=config.loop_window,
            loop_threshold=config.loop_threshold,
        )
        self.gateway = Gateway(config.providers, config.fallback_chain)

    def new_session(self) -> BreakerState:
        """Create a state object to track depth/budget across multiple calls."""
        return self.breaker.new_state()

    def complete(
        self,
        messages: Union[List[Message], List[Dict]],
        state: Optional[BreakerState] = None,
        **kwargs,
    ) -> Response:
        msgs = [Message(**m) if isinstance(m, dict) else m for m in messages]
        if state is None:
            state = self.breaker.new_state()

        # M1 pre-checks (loop / budget / depth)
        try:
            self.breaker.check_depth(state)
            self.breaker.check_budget(state)
            self.breaker.check_loop(state, msgs)
        except (LoopDetected, BudgetExceeded, MaxDepthExceeded) as e:
            log.warning("M1 blocked: %s", e)
            return Response(
                content="",
                provider="<blocked>",
                model="",
                usage=Usage(),
                blocked=True,
                block_reason=f"{type(e).__name__}: {e}",
            )

        self.breaker.increment_depth(state)

        # M5 call with fallback
        try:
            resp = self.gateway.call(msgs, **kwargs)
        except AllProvidersFailed as e:
            log.error("M5 exhausted: %s", e)
            return Response(
                content="",
                provider="<failed>",
                model="",
                usage=Usage(),
                blocked=True,
                block_reason=f"AllProvidersFailed: {e}",
            )

        # M1 post-record
        self.breaker.record_cost(state, resp.usage.cost_usd)
        return resp
