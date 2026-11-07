"""Provider abstraction."""
from abc import ABC, abstractmethod
from typing import List, Tuple
from ..types import Message, ProviderConfig, Usage


class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def complete(self, messages: List[Message], **kwargs) -> Tuple[str, Usage]:
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1000.0 * self.config.cost_per_1k_input
            + output_tokens / 1000.0 * self.config.cost_per_1k_output
        )
