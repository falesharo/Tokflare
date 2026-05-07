import aiohttp
import logging
from src.core.config import settings

class NOWPayments:
    def __init__(self):
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.base_url = "https://api.nowpayments.io/v1"

    async def create_payment(self, amount: float, currency: str, order_id: str):
        """
        Creates a payment on NOWPayments.
        """
        if not self.api_key:
            logging.warning("NOWPayments API key not found. Using mock payment data.")
            return {
                "payment_id": "MOCK_PAY_5678",
                "pay_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                "pay_amount": amount / 65000.0 if currency == "BTC" else amount / 3500.0
            }

        headers = {"x-api-key": self.api_key}
        payload = {
            "price_amount": amount,
            "price_currency": "usd",
            "pay_currency": currency.lower(),
            "order_id": order_id,
            "order_description": f"TokFlare Order #{order_id}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/payment", json=payload, headers=headers) as resp:
                return await resp.json()

    async def check_payment_status(self, payment_id: str):
        """
        Checks the status of a payment.
        """
        if not self.api_key:
            return "finished" # Mock status

        headers = {"x-api-key": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/payment/{payment_id}", headers=headers) as resp:
                result = await resp.json()
                return result.get("payment_status")
