from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.bot.ui.templates import Templates
from src.bot.ui.i18n import I18n
from src.bot.keyboards.inline import Keyboards
from src.database.models import User, Order, OrderStatus
from src.database.db import async_session
from src.core.config import settings
from src.bot.utils import update_app_screen
import os

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
                language=message.from_user.language_code if message.from_user.language_code in ["en", "fr"] else "en"
            )
            session.add(user)
            await session.commit()
        
        tier = user.tier if user else "BRONZE"
        lang = user.language if user else "en"
    
    text = Templates.welcome(message.from_user.first_name, tier, lang)
    markup = Keyboards.main_menu(lang)

    # Luxury Banner Check
    if os.path.exists(settings.LOGO_PATH):
        logo = types.FSInputFile(settings.LOGO_PATH)
        await message.answer_photo(photo=logo, caption=text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)

@router.callback_query(F.data == "back_main")
async def process_back_main(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        tier = user.tier if user else "BRONZE"
        lang = user.language if user else "en"

    await update_app_screen(callback.message, Templates.welcome(callback.from_user.first_name, tier, lang), Keyboards.main_menu(lang))

@router.callback_query(F.data == "support")
async def process_support(callback: types.CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        lang = user.language if user else "en"

    await update_app_screen(callback.message, I18n.t("support_text", lang) + f"\n\n{Templates.SEPARATOR}", Keyboards.back_to_main(lang))

@router.callback_query(F.data == "profile")
async def process_profile(callback: types.CallbackQuery):
    await callback.answer()
    
    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        lang = user.language if user else "en"
        stmt = select(Order).where(Order.user_id == callback.from_user.id)
        result = await session.execute(stmt)
        orders = result.scalars().all()
        total_spent = user.total_spent if user else 0.0
        tier = user.tier if user else "BRONZE"
        
    completed_orders = sum(1 for o in orders if o.status == OrderStatus.COMPLETED)
    
    profile_text = (
        f"{I18n.t('profile_title', lang)}\n\n"
        f"{I18n.t('profile_identifier', lang, id=callback.from_user.id)}\n"
        f"{I18n.t('profile_alias', lang, username=callback.from_user.username or 'unknown')}\n"
        f"{I18n.t('profile_rank', lang, tier=tier)}\n\n"
        f"{I18n.t('profile_stats', lang)}\n"
        f"{I18n.t('profile_deployments', lang, total=len(orders))}\n"
        f"{I18n.t('profile_success', lang, success=completed_orders)}\n"
        f"{I18n.t('profile_spent', lang, spent=total_spent)}\n\n"
        f"{Templates.SEPARATOR}"
    )
    
    await update_app_screen(
        callback.message,
        f"{Templates.BRAND_HEADER}\n{profile_text}",
        reply_markup=Keyboards.profile_menu(lang)
    )

@router.callback_query(F.data == "change_lang")
async def process_change_lang(callback: types.CallbackQuery):
    await callback.answer()
    async with async_session() as session:
        user = await session.get(User, callback.from_user.id)
        lang = user.language if user else "en"

    await update_app_screen(
        callback.message,
        f"{Templates.BRAND_HEADER}\n"
        f"{I18n.t('welcome', lang, name=callback.from_user.first_name, tier='Elite', icon='🌐', discount=0)}\n\n"
        "Please select your preferred interface language:",
        reply_markup=Keyboards.language_selection(lang)
    )

@router.callback_query(F.data.startswith("setlang_"))
async def set_language(callback: types.CallbackQuery, user: User):
    lang = callback.data.split("_")[1]
    
    async with async_session() as session:
        db_user = await session.get(User, user.id)
        db_user.language = lang
        await session.commit()
    
    await callback.answer(f"Language updated to {lang.upper()}", show_alert=True)
    await process_profile(callback)
