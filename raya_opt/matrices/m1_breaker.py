"""M1: Circuit Breaker.
- Loop detection via content hash counting in a sliding window
- Hard budget cap (USD)
- Recursive depth cap
"""
import hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List

from ..types import Message
from ..exceptions import LoopDetected, BudgetExceeded, MaxDepthExceeded


@dataclass
class BreakerState:
    depth: int = 0
    spent_usd: float = 0.0
    call_hashes: Deque[str] = field(default_factory=deque)


class CircuitBreaker:
    def __init__(
        self,
        budget_usd: float,
        max_depth: int,
        loop_window: int,
        loop_threshold: int,
    ):
        self.budget = budget_usd
        self.max_depth = max_depth
        self.window = loop_window
        self.threshold = loop_threshold

    def new_state(self) -> BreakerState:
        return BreakerState(call_hashes=deque(maxlen=self.window))

    def check_depth(self, state: BreakerState) -> None:
        if state.depth >= self.max_depth:
            raise MaxDepthExceeded(
                f"depth {state.depth} >= max {self.max_depth}"
            )

    def check_budget(self, state: BreakerState, projected_cost: float = 0.0) -> None:
        if state.spent_usd + projected_cost >= self.budget:
            raise BudgetExceeded(
                f"spent ${state.spent_usd:.4f} + projected ${projected_cost:.4f} "
                f">= cap ${self.budget:.4f}"
            )

    def check_loop(self, state: BreakerState, messages: List[Message]) -> None:
        h = self._hash_messages(messages)
        count = list(state.call_hashes).count(h) + 1  # include this call
        if count >= self.threshold:
            raise LoopDetected(
                f"same call {h[:8]} seen {count}× in window of {self.window}"
            )
        state.call_hashes.append(h)

    def record_cost(self, state: BreakerState, cost: float) -> None:
        state.spent_usd += cost

    def increment_depth(self, state: BreakerState) -> None:
        state.depth += 1

    @staticmethod
    def _hash_messages(messages: List[Message]) -> str:
        text = "\x1f".join(f"{m.role}\x1e{m.content}" for m in messages)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
