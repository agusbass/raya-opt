"""Raya-Opt: cost-aware LLM gateway with built-in circuit breaker."""
from .core import RayaOpt
from .config import Config
from .types import Message, ProviderConfig, Usage, Response
from .exceptions import (
    RayaOptError,
    LoopDetected,
    BudgetExceeded,
    MaxDepthExceeded,
    AllProvidersFailed,
)

__version__ = "0.1.0"
__all__ = [
    "RayaOpt",
    "Config",
    "Message",
    "ProviderConfig",
    "Usage",
    "Response",
    "RayaOptError",
    "LoopDetected",
    "BudgetExceeded",
    "MaxDepthExceeded",
    "AllProvidersFailed",
]
