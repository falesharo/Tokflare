import html
from src.bot.ui.i18n import I18n

class Templates:
    BRAND_HEADER = "<b>⚡️ T O K F L A R E   E L I T E</b>\n"
    SEPARATOR = "────────────────"
    
    TIER_DATA = {
        "BRONZE": {"icon": "🥉", "discount": 0.0, "next": 100},
        "SILVER": {"icon": "🥈", "discount": 0.05, "next": 500},
        "GOLD": {"icon": "🥇", "discount": 0.10, "next": 2000},
        "ELITE": {"icon": "💎", "discount": 0.20, "next": 0}
    }

    @classmethod
    def progress_bar(cls, current_step: int, total_steps: int = 3):
        """Generates a sleek minimalist progress bar."""
        full = "▬"
        empty = "▭"
        bar = ""
        for i in range(1, total_steps + 1):
            bar += full if i <= current_step else empty
        return f"<code>{bar}</code>  [ {current_step}/{total_steps} ]"

    @classmethod
    def welcome(cls, name: str, tier: str = "BRONZE", lang: str = "en"):
        t = cls.TIER_DATA.get(tier, cls.TIER_DATA["BRONZE"])
        content = I18n.t("welcome", lang, name=html.escape(name), tier=tier, icon=t['icon'], discount=int(t['discount']*100))
        return f"{cls.BRAND_HEADER}\n{content}\n\n{cls.SEPARATOR}\n{I18n.t('select_operation', lang)}"

    @classmethod
    def order_link(cls, product_name: str, description: str, lang: str = "en"):
        content = I18n.t("order_link", lang, name=product_name, description=description, progress=cls.progress_bar(1, 3))
        return f"{cls.BRAND_HEADER}\n{content}"

    @classmethod
    def order_quantity(cls, min_q: int, max_qty: int, lang: str = "en"):
        content = I18n.t("order_qty", lang, min=min_q, max=max_qty, progress=cls.progress_bar(2, 3))
        return f"{cls.BRAND_HEADER}\n{content}"

    @classmethod
    def order_summary_credit(cls, name: str, qty: int, price: float, balance: float, tier: str = "BRONZE", lang: str = "en"):
        t = cls.TIER_DATA.get(tier, cls.TIER_DATA["BRONZE"])
        discount_val = price * t['discount']
        final_price = price - discount_val
        
        content = I18n.t("order_confirm", lang, 
                        name=name, qty=qty, price=price, 
                        discount_val=discount_val, final_price=final_price, 
                        balance=balance, progress=cls.progress_bar(3, 3))
        return f"{cls.BRAND_HEADER}\n{content}"

    @classmethod
    def wallet_dashboard(cls, balance: float, tier: str, total_spent: float, lang: str = "en"):
        t = cls.TIER_DATA.get(tier, cls.TIER_DATA["BRONZE"])
        next_tier_info = ""
        if t['next'] > 0:
            remaining = t['next'] - total_spent
            # This is hard to translate inline without more keys, but let's keep it simple
            next_tier_info = f"\n<i>Reach ${t['next']} to unlock next rank (${remaining:.2f} to go)</i>"
            
        content = I18n.t("wallet_dashboard", lang, balance=balance, tier=tier, icon=t['icon'], total_spent=total_spent, next_tier_info=next_tier_info)
        recharge = I18n.t("recharge_bonuses", lang)
        
        return f"{cls.BRAND_HEADER}\n{content}\n\n{cls.SEPARATOR}\n{recharge}"

    @classmethod
    def order_success(cls, order_id: int, lang: str = "en"):
        # We should add a translation key for this too
        return (
            f"{cls.BRAND_HEADER}\n"
            "✅ <b>OPERATION INITIALIZED</b>\n\n"
            f"Order <code>#{order_id}</code> is currently being routed "
            "through our high-speed global nodes.\n\n"
            "<i>Status updates are streamed to your history.</i>"
        )
    
    @classmethod
    def payment_details(cls, amount: float, currency: str, address: str, lang: str = "en"):
        return (
            f"{cls.BRAND_HEADER}\n"
            "⏳ <b>Deposit Awaiting Confirmation</b>\n\n"
            f"Please send exactly:\n"
            f"<code>{amount} {currency}</code>\n\n"
            f"Recipient Address:\n"
            f"<code>{address}</code>\n\n"
            f"{cls.SEPARATOR}\n"
            "⚠️ <b>Important:</b>\n"
            "• Send only the specified asset.\n"
            "• Credits will be added after 1 blockchain confirmation.\n"
            "• This invoice expires in 60 minutes."
        )
