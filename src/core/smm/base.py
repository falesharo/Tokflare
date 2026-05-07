from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class ProviderStatus(Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    FAILED = "Failed"

@dataclass
class ProviderResponse:
    order_id: str
    raw_response: dict

class BaseSMMProvider(ABC):
    @abstractmethod
    async def submit_order(self, service_id: str, link: str, comments: list[str]) -> ProviderResponse:
        """Submit a new order to the provider."""
        pass

    @abstractmethod
    async def get_status(self, provider_order_id: str) -> ProviderStatus:
        """Check the status of an existing order."""
        pass

    @abstractmethod
    async def get_service_price(self, service_id: str) -> float:
        """Get the current cost for a specific service."""
        pass
