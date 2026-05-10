import aiohttp
import logging
from src.core.smm.base import BaseSMMProvider, ProviderResponse, ProviderStatus

class SMMWizProvider(BaseSMMProvider):
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    async def submit_order(self, service_id: str, link: str, quantity: int = None, 
                           comments: list[str] = None, drip_feed: bool = False, 
                           runs: int = None, interval: int = None) -> ProviderResponse:
        params = {
            'key': self.api_key,
            'action': 'add',
            'service': service_id,
            'link': link
        }
        
        if comments:
            params['comments'] = '\n'.join(comments)
        elif quantity:
            params['quantity'] = quantity
        
        # Support Drip-Feed
        if drip_feed and runs and interval:
            params['runs'] = runs
            params['interval'] = interval

        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, data=params) as resp:
                result = await resp.json()
                if 'order' in result:
                    return ProviderResponse(order_id=str(result['order']), raw_response=result)
                raise Exception(f"SMMWiz Error: {result.get('error', 'Unknown error')}")

    async def get_status(self, provider_order_id: str) -> ProviderStatus:
        params = {
            'key': self.api_key,
            'action': 'status',
            'order': provider_order_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, data=params) as resp:
                result = await resp.json()
                status_map = {
                    'Pending': ProviderStatus.PENDING,
                    'Processing': ProviderStatus.PROCESSING,
                    'Completed': ProviderStatus.COMPLETED,
                    'Canceled': ProviderStatus.CANCELLED,
                    'Fail': ProviderStatus.FAILED
                }
                return status_map.get(result.get('status'), ProviderStatus.PENDING)

    async def get_service_price(self, service_id: str) -> float:
        services = await self.get_all_services()
        for service in services:
            if str(service.get('service')) == str(service_id):
                return float(service.get('rate', 0.10))
        return 0.10

    async def get_all_services(self) -> list[dict]:
        params = {'key': self.api_key, 'action': 'services'}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, data=params) as resp:
                return await resp.json()
