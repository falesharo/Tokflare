import aiohttp
import logging
from src.core.config import settings

class SMMPanel:
    def __init__(self):
        self.url = settings.SMM_API_URL
        self.key = settings.SMM_API_KEY

    async def submit_order(self, link: str, comments: list[str]) -> str:
        """
        Submits an order to the SMM panel.
        Returns the external order ID.
        """
        if not self.url or not self.key:
            logging.warning("SMM API not configured. Simulating order submission.")
            return "MOCK_ORDER_12345"

        params = {
            'key': self.key,
            'action': 'add',
            'service': '123', # Example service ID for custom TikTok comments
            'link': link,
            'comments': '\n'.join(comments)
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=params) as resp:
                result = await resp.json()
                if 'order' in result:
                    return str(result['order'])
                else:
                    raise Exception(f"SMM Panel Error: {result.get('error', 'Unknown error')}")

    async def get_status(self, external_id: str) -> str:
        """
        Fetches the status of an order from the SMM panel.
        """
        if not self.url or not self.key:
            return "Completed" # Mock status

        params = {
            'key': self.key,
            'action': 'status',
            'order': external_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data=params) as resp:
                result = await resp.json()
                return result.get('status', 'Pending')
