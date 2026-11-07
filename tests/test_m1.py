"""Tests for M1 circuit breaker."""
import pytest

from raya_opt.matrices.m1_breaker import CircuitBreaker
from raya_opt.types import Message
from raya_opt.exceptions import LoopDetected, BudgetExceeded, MaxDepthExceeded


def make_breaker(**overrides):
    defaults = dict(budget_usd=1.0, max_depth=3, loop_window=4, loop_threshold=3)
    defaults.update(overrides)
    return CircuitBreaker(**defaults)


def test_depth_ok():
    b = make_breaker()
    s = b.new_state()
    b.check_depth(s)


def test_depth_exceeded():
    b = make_breaker(max_depth=3)
    s = b.new_state()
    s.depth = 3
    with pytest.raises(MaxDepthExceeded):
        b.check_depth(s)


def test_budget_ok():
    b = make_breaker(budget_usd=0.5)
    s = b.new_state()
    s.spent_usd = 0.4
    b.check_budget(s, projected_cost=0.05)


def test_budget_exceeded():
    b = make_breaker(budget_usd=0.5)
    s = b.new_state()
    s.spent_usd = 0.49
    with pytest.raises(BudgetExceeded):
        b.check_budget(s, projected_cost=0.05)


def test_loop_distinct_calls_ok():
    b = make_breaker(loop_threshold=3, loop_window=5)
    s = b.new_state()
    for i in range(5):
        b.check_loop(s, [Message(role="user", content=f"q{i}")])


def test_loop_detected_on_third_repeat():
    b = make_breaker(loop_threshold=3, loop_window=5)
    s = b.new_state()
    msgs = [Message(role="user", content="ping")]
    b.check_loop(s, msgs)
    b.check_loop(s, msgs)
    with pytest.raises(LoopDetected):
        b.check_loop(s, msgs)


def test_record_cost_accumulates():
    b = make_breaker()
    s = b.new_state()
    b.record_cost(s, 0.01)
    b.record_cost(s, 0.02)
    assert s.spent_usd == pytest.approx(0.03)
