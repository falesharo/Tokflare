from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Keyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🛒 New Order", callback_data="order_new"))
        builder.row(
            InlineKeyboardButton(text="📜 History", callback_data="order_history"),
            InlineKeyboardButton(text="👤 Profile", callback_data="profile")
        )
        builder.row(InlineKeyboardButton(text="🆘 Support", callback_data="support"))
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
        builder.row(InlineKeyboardButton(text="❌ Cancel", callback_data="order_cancel"))
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
    def order_tracking(order_id: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="🔄 Refresh Status", callback_data=f"track_{order_id}"))
        return builder.as_markup()
