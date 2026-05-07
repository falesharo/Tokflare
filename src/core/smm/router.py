from typing import Dict, Optional
from src.core.smm.base import BaseSMMProvider
from src.core.smm.providers.smmwiz import SMMWizProvider
from src.core.config import settings

class ProviderRouter:
    def __init__(self):
        self._providers: Dict[str, BaseSMMProvider] = {}
        self._active_provider_name: Optional[str] = None
        
        # Auto-initialize from settings
        if settings.SMM_API_URL and settings.SMM_API_KEY:
            self.register_provider("smmwiz", SMMWizProvider(settings.SMM_API_URL, settings.SMM_API_KEY))
            self.set_active_provider("smmwiz")

    def register_provider(self, name: str, provider: BaseSMMProvider):
        self._providers[name] = provider

    def set_active_provider(self, name: str):
        if name in self._providers:
            self._active_provider_name = name
        else:
            raise ValueError(f"Provider {name} not registered.")

    def get_provider(self, name: Optional[str] = None) -> BaseSMMProvider:
        name = name or self._active_provider_name
        if not name or name not in self._providers:
            raise Exception("No active SMM provider configured.")
        return self._providers[name]

    @property
    def active_provider_name(self) -> str:
        return self._active_provider_name or "None"

smm_router = ProviderRouter()
