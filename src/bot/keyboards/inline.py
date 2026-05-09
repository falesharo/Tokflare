from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Keyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🛒 New Order", callback_data="order_new"))
        builder.row(
            InlineKeyboardButton(text="📜 History", callback_data="order_history"),
            InlineKeyboardButton(text="💳 Wallet", callback_data="wallet")
        )
        builder.row(
            InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
            InlineKeyboardButton(text="🆘 Support", callback_data="support")
        )
        return builder.as_markup()

    @staticmethod
    def wallet_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="➕ Deposit Funds", callback_data="deposit"))
        builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def back_to_wallet() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Back to Wallet", callback_data="wallet"))
        return builder.as_markup()

    @staticmethod
    def platforms(platform_list: list[str]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for p in platform_list:
            builder.row(InlineKeyboardButton(text=f"🌐 {p}", callback_data=f"plat_{p}"))
        builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def cancel_order() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="❌ Cancel Order", callback_data="order_cancel"))
        return builder.as_markup()

    @staticmethod
    def confirm_order() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="✅ Confirm & Pay", callback_data="order_confirm"))
        builder.row(
            InlineKeyboardButton(text="🔙 Back", callback_data="order_new"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="order_cancel")
        )
        return builder.as_markup()

    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="Bitcoin (BTC)", callback_data="pay_btc"),
            InlineKeyboardButton(text="Ethereum (ETH)", callback_data="pay_eth")
        )
        builder.row(
            InlineKeyboardButton(text="USDT (TRC20)", callback_data="pay_usdttrc20"),
            InlineKeyboardButton(text="Litecoin (LTC)", callback_data="pay_ltc")
        )
        builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="order_new"))
        return builder.as_markup()

    @staticmethod
    def back_to_main() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def order_tracking(order_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 Refresh Status", callback_data=f"track_{order_id}"))
        builder.row(InlineKeyboardButton(text="🔙 Back to Main", callback_data="back_main"))
        return builder.as_markup()
