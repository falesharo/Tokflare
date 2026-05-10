import re
from typing import Tuple, List

class OrderService:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validates any social media URL."""
        if not url: return False
        return bool(re.match(r'https?://[^\s]+', url))

    @staticmethod
    def parse_comments(text: str) -> List[str]:
        """Parses comments from a multi-line or comma-separated string."""
        if not text: return []
        if ',' in text and '\n' not in text:
            return [c.strip() for c in text.split(',') if c.strip()]
        return [c.strip() for c in text.split('\n') if c.strip()]

    @staticmethod
    def calculate_price(qty: int, rate_per_1000: float, tier: str = "BRONZE") -> Tuple[float, float]:
        """Calculates total price and discount based on user tier."""
        from src.bot.ui.templates import Templates
        t_data = Templates.TIER_DATA.get(tier, Templates.TIER_DATA["BRONZE"])
        
        raw_price = (qty / 1000.0) * rate_per_1000
        discount = raw_price * t_data['discount']
        final_price = raw_price - discount
        
        return final_price, discount
