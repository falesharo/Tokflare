import re
from typing import List, Tuple
from src.core.config import settings
from src.core.smm.router import smm_router

class OrderService:
    @staticmethod
    def parse_comments(text: str) -> List[str]:
        """Parse comments separated by newlines or commas."""
        if ',' in text and '\n' not in text:
            comments = [c.strip() for c in text.split(',')]
        else:
            comments = [c.strip() for c in text.split('\n')]
        return [c for c in comments if c]

    @staticmethod
    def validate_comments(comments: List[str]) -> Tuple[bool, str]:
        """Validate comment count and content."""
        count = len(comments)
        if count < 5:
            return False, "❌ <b>Too Few Comments</b>\nPlease provide at least 5 comments."
        if count > 1000:
            return False, "❌ <b>Too Many Comments</b>\nMaximum is 1000 comments."
        return True, ""

    @staticmethod
    async def calculate_price(comment_count: int, service_id: str = "123") -> Tuple[float, float]:
        """
        Calculate total price with dynamic margin.
        Returns (total_price, provider_cost).
        """
        try:
            provider = smm_router.get_provider()
            cost_per_unit = await provider.get_service_price(service_id)
        except:
            cost_per_unit = 0.05 # Fallback cost
            
        provider_cost = comment_count * cost_per_unit
        # Add dynamic margin from settings
        total_price = provider_cost * settings.PROFIT_MARGIN
        
        # Apply a minimum price if needed
        total_price = max(total_price, 0.50)
        
        return round(total_price, 2), round(provider_cost, 4)

    @staticmethod
    def validate_tiktok_url(url: str) -> bool:
        pattern = re.compile(r'(https?://)?(www\.)?tiktok\.com/.+')
        return bool(pattern.match(url))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL for different platforms."""
        patterns = {
            'tiktok': r'(https?://)?(www\.)?tiktok\.com/.+',
            'instagram': r'(https?://)?(www\.)?instagram\.com/.+',
            'youtube': r'(https?://)?(www\.)?youtube\.com/.+',
            'facebook': r'(https?://)?(www\.)?facebook\.com/.+',
            'twitter': r'(https?://)?(www\.)?twitter\.com/.+',
        }
        for pattern in patterns.values():
            if re.compile(pattern).match(url):
                return True
        return False
