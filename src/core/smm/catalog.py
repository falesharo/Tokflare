from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class TokFlareProduct:
    id: str  # Internal ID
    display_name: str
    description: str
    link_hint: str # Specific instruction for the URL
    smm_service_id: str  # The real ID from SMMWiz
    category: str # Likes, Followers, etc.
    platform: str # TikTok, Instagram, etc.

# THE ELITE CATALOG (1-to-1 Mapping)
# Short elegant names for buttons, full details in description
ELITE_CATALOG = [
    # INSTAGRAM
    TokFlareProduct(
        id="ig_followers_elite",
        display_name="👤 Elite Followers",
        description="💎 QUALITY: Real Accounts [HQ]\n🌍 REGION: Global\n🛡️ WARRANTY: 30 Days Refill",
        link_hint="IG_PROFILE",
        smm_service_id="20888",
        category="Followers 👤",
        platform="Instagram"
    ),
    TokFlareProduct(
        id="ig_followers_usa",
        display_name="👤 USA Followers",
        description="💎 QUALITY: Organic Profiles\n🌍 REGION: United States 🇺🇸\n⚡ SPEED: High Retention",
        link_hint="IG_PROFILE",
        smm_service_id="4016",
        category="Followers 👤",
        platform="Instagram"
    ),
    TokFlareProduct(
        id="ig_likes_organic",
        display_name="❤️ Organic Likes",
        description="💎 QUALITY: Real Active Users\n⚡ SPEED: Instant Delivery\n🚀 IMPACT: Explore Page Boost",
        link_hint="IG_POST",
        smm_service_id="17702",
        category="Likes ❤️",
        platform="Instagram"
    ),
    
    # TIKTOK
    TokFlareProduct(
        id="tk_followers_premium",
        display_name="👤 Premium Followers",
        description="💎 QUALITY: Elite Profiles\n🛡️ WARRANTY: Lifetime Guarantee\n⚡ SPEED: Instant Start",
        link_hint="TT_PROFILE",
        smm_service_id="12850",
        category="Followers 👤",
        platform="TikTok"
    ),
    TokFlareProduct(
        id="tk_likes_hq",
        display_name="❤️ Viral Hearts",
        description="💎 QUALITY: High-Quality Profiles\n⚡ SPEED: Express Delivery\n🔥 IMPACT: Viral Momentum",
        link_hint="TT_VIDEO",
        smm_service_id="12351",
        category="Likes ❤️",
        platform="TikTok"
    ),
    TokFlareProduct(
        id="tk_comments_custom",
        display_name="💬 Elite Comments",
        description="💎 QUALITY: Real Active Audience\n✍️ TYPE: 100% Custom Input\n🛡️ SAFETY: Safe & Secure",
        link_hint="TT_VIDEO",
        smm_service_id="20176",
        category="Comments 💬",
        platform="TikTok"
    ),
    
    # TELEGRAM
    TokFlareProduct(
        id="tg_members_premium",
        display_name="👤 Star Members ⭐️",
        description="💎 QUALITY: Premium Verified Accounts\n📈 IMPACT: Maximum Channel Authority\n🛡️ WARRANTY: Ultra Stable",
        link_hint="TG_CHANNEL",
        smm_service_id="20839",
        category="Members 👥",
        platform="Telegram"
    ),
    TokFlareProduct(
        id="tg_views_instant",
        display_name="👁️ Instant Views",
        description="💎 QUALITY: Real Post Interactions\n⚡ SPEED: 0-5 min Start\n🌍 REGION: Global Reach",
        link_hint="TG_POST",
        smm_service_id="19763",
        category="Views 👁️",
        platform="Telegram"
    ),
    
    # YOUTUBE
    TokFlareProduct(
        id="yt_views_organic",
        display_name="👁️ Organic Views",
        description="💎 QUALITY: High Retention Watch-time\n📈 IMPACT: SEO & Search Ranking\n🛡️ WARRANTY: Guaranteed",
        link_hint="YT_VIDEO",
        smm_service_id="12950",
        category="Views 👁️",
        platform="YouTube"
    ),
    TokFlareProduct(
        id="yt_subscribers_auth",
        display_name="👤 Elite Subscribers",
        description="💎 QUALITY: Authentic Channels\n🛡️ WARRANTY: 100% Non-Drop Lifetime\n🔥 IMPACT: Channel Authority",
        link_hint="YT_CHANNEL",
        smm_service_id="19827",
        category="Subscribers 🔔",
        platform="YouTube"
    ),
]

class CatalogManager:
    @staticmethod
    def get_platforms() -> List[str]:
        return sorted(list(set(p.platform for p in ELITE_CATALOG)))

    @staticmethod
    def get_actions(platform: str) -> List[str]:
        return sorted(list(set(p.category for p in ELITE_CATALOG if p.platform == platform)))

    @staticmethod
    def get_products(platform: str, category: str) -> List[TokFlareProduct]:
        return [p for p in ELITE_CATALOG if p.platform == platform and p.category == category]

    @staticmethod
    def get_product_by_id(product_id: str) -> Optional[TokFlareProduct]:
        for p in ELITE_CATALOG:
            if p.id == product_id:
                return p
        return None
