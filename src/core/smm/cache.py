import logging
import re
from typing import Dict, List, Optional
from src.core.smm.router import smm_router
from src.core.config import settings

logger = logging.getLogger(__name__)

class ServiceCache:
    _instance = None
    _services: List[dict] = []
    _structured_catalog: Dict[str, Dict[str, List[dict]]] = {}
    _platforms: List[str] = []

    # MANUAL RENAMING MAP (For the "1 to 1" feel on top services)
    # Key: Service ID or specific keyword combo
    # Value: Professional Name
    CURATED_NAMES = {
        "tiktok_followers_hq": "Elite Real Followers [High-Speed]",
        "insta_likes_real": "Organic Impression Likes [Instant]",
        "views_retention": "High-Retention viral Views",
        "tiktok_comments_custom": "Custom Comments [High-Quality]",
        "insta_followers_premium": "Premium Followers [Instant Delivery]",
        "youtube_views_hq": "High-Quality Views [Fast Delivery]",
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceCache, cls).__new__(cls)
        return cls._instance

    def get_action_type(self, category: str, name: str) -> str:
        """Detects if service is Likes, Followers, Views, etc."""
        text = (category + " " + name).lower()
        if "follower" in text: return "Followers 👤"
        if "like" in text or "heart" in text: return "Likes ❤️"
        if "view" in text or "play" in text: return "Views 👁️"
        if "comment" in text: return "Comments 💬"
        if "share" in text or "repost" in text: return "Shares 🚀"
        if "subscriber" in text: return "Subscribers 🔔"
        return "Other Services 🛠️"

    def elite_cleaner(self, service: dict, platform: str) -> str:
        """The 'Human' touch cleaner for SaaS Elite."""
        name = service.get('name', '')
        # Check if we have a manual override for this ID
        svc_id = str(service.get('service'))
        if svc_id in self.CURATED_NAMES:
            return self.CURATED_NAMES[svc_id]

        # Professional Transformation Logic
        # Extract Quality
        quality = "Standard"
        if re.search(r'HQ|High Quality|Real|Active', name, re.I): quality = "Premium"
        if re.search(r'Elite|VIP|VHQ', name, re.I): quality = "Elite"
        if re.search(r'Cheap|Low', name, re.I): quality = "Basic"

        # Extract Speed
        speed = ""
        if re.search(r'Instant|Fast|Super', name, re.I): speed = " • Instant"
        
        # Extract Refill
        refill = ""
        if re.search(r'Refill|Stable|Lifetime|AR\d+', name, re.I): refill = " • Guaranteed"

        # Location
        loc_match = re.search(r'France|USA|Global|Turkey|Brazil|Arab', name, re.I)
        location = f"({loc_match.group(0)})" if loc_match else "(Global)"

        # Action Core (Followers, Likes, etc)
        action = self.get_action_type("", name).split(' ')[0]
        
        return f"{quality} {action}{speed}{refill} {location}"

    async def refresh_cache(self):
        """Fetches, filters and builds a professional structured catalog."""
        try:
            provider = smm_router.get_provider()
            raw_services = await provider.get_all_services()
            
            if not isinstance(raw_services, list):
                logger.error("Invalid SMM API response")
                return

            self._services = []
            catalog = {}
            platforms = set()

            for s in raw_services:
                name = s.get('name', '')
                cat_name = s.get('category', '')
                
                 # 1. STRICT FILTERING (Remove garbage)
                if any(x in (name + cat_name).lower() for x in ['test', 'beta', 'slow', 'down', 'dead', 'no refill', 'low quality', 'scam', 'fake']):
                    continue
                
                 # 2. Platform Detection
                platform = "Other"
                if "TikTok" in cat_name: platform = "TikTok"
                elif "Instagram" in cat_name: platform = "Instagram"
                elif "YouTube" in cat_name: platform = "YouTube"
                elif "Telegram" in cat_name: platform = "Telegram"
                elif "Facebook" in cat_name: platform = "Facebook"
                elif "Twitter" in cat_name: platform = "Twitter"
                elif "LinkedIn" in cat_name: platform = "LinkedIn"
                
                if platform == "Other": continue # Only professional platforms
                
                platforms.add(platform)
                action = self.get_action_type(cat_name, name)
                
                 # 3. Apply Pricing & SaaS Name
                rate = float(s.get('rate', 0))
                s['user_price_per_1000'] = rate * settings.PROFIT_MARGIN
                s['display_name'] = self.elite_cleaner(s, platform)
                
                # Add additional metadata for better service description
                s['description'] = s.get('name', '')
                s['min'] = int(s.get('min', 10))
                s['max'] = int(s.get('max', 10000))
                
                # 4. Structure: Platform -> Action -> [Services]
                if platform not in catalog: catalog[platform] = {}
                if action not in catalog[platform]: catalog[platform][action] = []
                
                # Limit to top 15 best services per action to avoid pollution
                if len(catalog[platform][action]) < 15:
                    catalog[platform][action].append(s)
                    self._services.append(s)

            self._structured_catalog = catalog
            self._platforms = sorted(list(platforms))
            logger.info(f"Elite Catalog Built: {len(self._platforms)} platforms active.")

        except Exception as e:
            logger.error(f"Cache Refresh Error: {e}")

    def get_platforms(self) -> List[str]:
        return self._platforms

    def get_actions(self, platform: str) -> List[str]:
        return sorted(list(self._structured_catalog.get(platform, {}).keys()))

    def get_services(self, platform: str, action: str) -> List[dict]:
        return self._structured_catalog.get(platform, {}).get(action, [])

    def get_service_details(self, service_id: str) -> dict:
        for s in self._services:
            if str(s.get('service')) == str(service_id):
                return s
        return {}

service_cache = ServiceCache()
