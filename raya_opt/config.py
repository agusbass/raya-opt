"""Library configuration."""
from dataclasses import dataclass
from typing import List
from .types import ProviderConfig


@dataclass
class Config:
    providers: List[ProviderConfig]
    fallback_chain: List[str]
    budget_usd: float = 1.0
    max_depth: int = 5
    loop_window: int = 6           # how many recent hashes to keep
    loop_threshold: int = 3        # same hash >= N times => loop
    request_timeout: float = 60.0
