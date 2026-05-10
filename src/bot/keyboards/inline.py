from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.bot.ui.i18n import I18n

class Keyboards:
    @staticmethod
    def main_menu(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_new_order", lang), callback_data="order_new"))
        builder.row(
            InlineKeyboardButton(text=I18n.t("btn_history", lang), callback_data="order_history"),
            InlineKeyboardButton(text=I18n.t("btn_wallet", lang), callback_data="wallet")
        )
        builder.row(
            InlineKeyboardButton(text=I18n.t("btn_profile", lang), callback_data="profile"),
            InlineKeyboardButton(text=I18n.t("btn_support", lang), callback_data="support")
        )
        return builder.as_markup()

    @staticmethod
    def wallet_menu(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_deposit", lang), callback_data="deposit"))
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def language_selection(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="English 🇺🇸", callback_data="setlang_en"),
            InlineKeyboardButton(text="Français 🇫🇷", callback_data="setlang_fr")
        )
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="profile"))
        return builder.as_markup()

    @staticmethod
    def back_to_wallet(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back_wallet", lang), callback_data="wallet"))
        return builder.as_markup()

    @staticmethod
    def platforms(platform_list: list[str], lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for p in platform_list:
            builder.row(InlineKeyboardButton(text=f"🌐 {p}", callback_data=f"plat_{p}"))
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def cancel_order(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_cancel", lang), callback_data="order_cancel"))
        return builder.as_markup()

    @staticmethod
    def confirm_order(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_confirm_pay", lang), callback_data="order_confirm"))
        builder.row(
            InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="order_new"),
            InlineKeyboardButton(text=I18n.t("btn_cancel", lang), callback_data="order_cancel")
        )
        return builder.as_markup()

    @staticmethod
    def payment_methods(back_callback: str = "order_new", lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="Bitcoin (BTC)", callback_data="pay_btc"),
            InlineKeyboardButton(text="Ethereum (ETH)", callback_data="pay_eth")
        )
        builder.row(
            InlineKeyboardButton(text="USDT (TRC20)", callback_data="pay_usdttrc20"),
            InlineKeyboardButton(text="Litecoin (LTC)", callback_data="pay_ltc")
        )
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data=back_callback))
        return builder.as_markup()

    @staticmethod
    def back_to_main(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back_main", lang), callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def profile_menu(lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_change_lang", lang), callback_data="change_lang"))
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back_main", lang), callback_data="back_main"))
        return builder.as_markup()

    @staticmethod
    def order_tracking(order_id: int, lang: str = "en") -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=I18n.t("btn_refresh", lang), callback_data=f"track_{order_id}"))
        builder.row(InlineKeyboardButton(text=I18n.t("btn_back_main", lang), callback_data="back_main"))
        return builder.as_markup()
