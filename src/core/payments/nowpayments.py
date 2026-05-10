import aiohttp
import logging
import hashlib
import hmac
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
                "pay_amount": amount / 65000.0 if currency == "BTC" else amount / 3500.0,
                "payment_status": "waiting"
            }

        headers = {"x-api-key": self.api_key}
        payload = {
            "price_amount": amount,
            "price_currency": "usd",
            "pay_currency": currency.lower(),
            "order_id": order_id,
            "order_description": f"TokFlare Order #{order_id}"
        }
        
        if hasattr(settings, 'NOWPAYMENTS_IPN_CALLBACK') and settings.NOWPAYMENTS_IPN_CALLBACK:
            payload["ipn_callback_url"] = settings.NOWPAYMENTS_IPN_CALLBACK

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/payment", json=payload, headers=headers) as resp:
                result = await resp.json()
                if resp.status == 200 or resp.status == 201:
                    return result
                else:
                    logging.error(f"NOWPayments API error {resp.status}: {result}")
                    return {"error": result.get('message', 'Payment creation failed')}

    async def check_payment_status(self, payment_id: str):
        """
        Checks the status of a payment.
        """
        if not self.api_key:
            return "waiting" # Do not auto-confirm in mock mode

        headers = {"x-api-key": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/payment/{payment_id}", headers=headers) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("payment_status", "failed")
                else:
                    return "failed"
    
    def verify_ipn(self, data: dict, signature: str) -> bool:
        """
        Verify NOWPayments IPN signature.
        """
        if not settings.NOWPAYMENTS_IPN_SECRET:
            return False
        
        # Create signature
        sorted_data = {k: v for k, v in sorted(data.items()) if k != "signature"}
        message = "&".join([f"{k}={v}" for k, v in sorted_data.items()])
        secret_bytes = bytes(settings.NOWPAYMENTS_IPN_SECRET, 'utf-8')
        message_bytes = bytes(message, 'utf-8')
        
        generated_signature = hmac.new(secret_bytes, message_bytes, hashlib.sha512).hexdigest()
        
        return hmac.compare_digest(generated_signature, signature)
