import html

class Templates:
    BRAND_HEADER = "<b>✨ T O K F L A R E ✨</b>\n<i>Premium TikTok Automation</i>\n"
    SEPARATOR = "────────────────────"
    
    @classmethod
    def welcome(cls, name: str):
        return (
            f"{cls.BRAND_HEADER}\n"
            f"Welcome back, <b>{html.escape(name)}</b>!\n\n"
            "Boost your TikTok presence with high-quality, custom comments "
            "delivered via our professional multi-provider network.\n\n"
            "🚀 <b>Ultra-Fast Delivery</b>\n"
            "🔒 <b>Secure Crypto Infrastructure</b>\n"
            "📊 <b>Real-time Order Tracking</b>\n\n"
            f"{cls.SEPARATOR}\n"
            "Select an option below to get started:"
        )

    @classmethod
    def order_link(cls):
        return (
            f"{cls.BRAND_HEADER}\n"
            "🔗 <b>Step 1/4: Link</b>\n"
            "📍 <code>Video URL Required</code>\n\n"
            "Please send the <b>link</b> to the TikTok video you want to boost.\n\n"
            "<i>Example: https://www.tiktok.com/@user/video/1234567890</i>"
        )

    @classmethod
    def order_comments(cls, min_c: int, max_c: int):
        return (
            f"{cls.BRAND_HEADER}\n"
            "✍️ <b>Step 2/4: Content</b>\n"
            "📍 <code>Custom Comments</code>\n\n"
            "Please send your custom comments.\n"
            f"Minimum: <b>{min_c}</b> | Maximum: <b>{max_c}</b>\n\n"
            "💡 <i>You can separate comments by <b>new lines</b> or <b>commas</b>.</i>"
        )

    @classmethod
    def order_summary(cls, link: str, count: int, price: float):
        return (
            f"{cls.BRAND_HEADER}\n"
            "📋 <b>Step 3/4: Verification</b>\n"
            "📍 <code>Order Review</code>\n\n"
            f"🔗 <b>Target:</b> <code>{link}</code>\n"
            f"💬 <b>Quantity:</b> <code>{count} comments</code>\n"
            f"💰 <b>Total Amount:</b> <code>${price:.2f}</code>\n\n"
            f"{cls.SEPARATOR}\n"
            "Please confirm the details to generate your payment invoice."
        )

    @classmethod
    def payment_selection(cls):
        return (
            f"{cls.BRAND_HEADER}\n"
            "💳 <b>Step 4/4: Settlement</b>\n"
            "📍 <code>Payment Gateway</code>\n\n"
            "Select your preferred cryptocurrency to finalize the order.\n"
            "Your transaction will be tracked live on the blockchain."
        )

    @classmethod
    def payment_details(cls, amount: float, currency: str, address: str):
        return (
            f"{cls.BRAND_HEADER}\n"
            "⏳ <b>Awaiting Confirmation</b>\n"
            "📍 <code>Blockchain Ledger</code>\n\n"
            f"Please send exactly:\n"
            f"<code>{amount} {currency}</code>\n\n"
            f"Recipient Address:\n"
            f"<code>{address}</code>\n\n"
            f"{cls.SEPARATOR}\n"
            "⚠️ <b>Important:</b>\n"
            "• Send only the specified asset.\n"
            "• Order will auto-process after 1 confirmation.\n"
            "• This invoice expires in 60 minutes."
        )

    @classmethod
    def status_update(cls, order_id: int, status: str, link: str):
        status_emoji = {
            "pending": "⏳",
            "processing": "⚙️",
            "completed": "✨",
            "failed": "❌"
        }.get(status.lower(), "🔄")
        
        return (
            f"{cls.BRAND_HEADER}\n"
            f"📦 <b>Order #{order_id} Update</b>\n\n"
            f"📊 <b>Status:</b> {status_emoji} {status.upper()}\n"
            f"🔗 <b>Target:</b> {link}\n\n"
            f"{cls.SEPARATOR}\n"
            "<i>Status is updated automatically every minute.</i>"
        )
