import logging
from typing import Dict, List, Optional
from src.core.smm.router import smm_router
from src.core.config import settings
from src.core.smm.catalog import ELITE_CATALOG

logger = logging.getLogger(__name__)

class ServiceCache:
    """
    Handles real-time data from the SMM provider (prices, limits).
    STRICTLY caches only services defined in the ELITE_CATALOG.
    """
    _instance = None
    _services: Dict[str, dict] = {} # Map SMM_ID -> Data

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceCache, cls).__new__(cls)
        return cls._instance

    async def refresh_cache(self):
        """Fetches latest prices and limits ONLY for validated elite services."""
        try:
            provider = smm_router.get_provider()
            raw_services = await provider.get_all_services()
            
            if not isinstance(raw_services, list):
                logger.error("Invalid SMM API response format.")
                return

            # Get the list of IDs we actually care about
            validated_ids = {str(p.smm_service_id) for p in ELITE_CATALOG}
            
            processed_count = 0
            new_cache = {}

            for s in raw_services:
                smm_id = str(s.get('service'))
                if smm_id in validated_ids:
                    rate = float(s.get('rate', 0))
                    # Store calculated user price
                    s['user_price_per_1000'] = rate * settings.PROFIT_MARGIN
                    new_cache[smm_id] = s
                    processed_count += 1

            self._services = new_cache
            logger.info(f"Elite Cache Refreshed: {processed_count} validated services active.")

            if processed_count < len(validated_ids):
                missing = validated_ids - set(new_cache.keys())
                logger.warning(f"Some elite services are missing from provider: {missing}")

        except Exception as e:
            logger.error(f"Elite Cache Refresh Error: {e}")

    def get_service_details(self, smm_id: str) -> dict:
        """Returns provider data for a specific SMM service ID."""
        return self._services.get(str(smm_id), {})

service_cache = ServiceCache()
