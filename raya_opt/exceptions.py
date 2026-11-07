"""Raya-Opt exception hierarchy."""


class RayaOptError(Exception):
    """Base error."""


class LoopDetected(RayaOptError):
    """M1: same call repeated beyond threshold."""


class BudgetExceeded(RayaOptError):
    """M1: cost ceiling hit."""


class MaxDepthExceeded(RayaOptError):
    """M1: recursive call depth exceeded."""


class AllProvidersFailed(RayaOptError):
    """M5: every provider in fallback chain failed."""
