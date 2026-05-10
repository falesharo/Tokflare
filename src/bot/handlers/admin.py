from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func, or_
from src.database.db import async_session
from src.database.models import Order, User, OrderStatus, Transaction, TransactionType
from src.core.config import settings
from src.bot.keyboards.inline import Keyboards
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.bot.ui.templates import Templates
from src.bot.ui.i18n import I18n
from src.bot.utils import update_app_screen
from src.core.admin_config import admin_settings
import logging

router = Router()
logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_for_margin = State()
    waiting_for_user_search = State()
    waiting_for_balance_change = State()
    waiting_for_ticket_reply = State()

def is_admin(user_id: int):
    return user_id in settings.ADMIN_IDS

async def cleanup_input(message: types.Message):
    try: await message.delete()
    except Exception: pass

# --- MAIN DASHBOARD ---

@router.message(Command("admin"))
async def admin_panel_root(message: types.Message, state: FSMContext, user: User):
    if not is_admin(message.from_user.id): return
    await state.clear()
    lang = user.language
    
    async with async_session() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar() or 0
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar() or 0
        total_revenue = (await session.execute(select(func.sum(Order.total_price)).where(Order.status == OrderStatus.COMPLETED))).scalar() or 0.0
        total_deposits = (await session.execute(select(func.sum(Transaction.amount_usd)).where(Transaction.type == TransactionType.DEPOSIT))).scalar() or 0.0

    builder = InlineKeyboardBuilder()
    test_mode_emoji = "🟢" if admin_settings.test_mode else "🔴"
    
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_test_mode", lang, emoji=test_mode_emoji), callback_data="admin_toggle_test"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_margin", lang, margin=admin_settings.profit_margin), callback_data="admin_set_margin"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_manage_users", lang), callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_recent_orders", lang), callback_data="admin_orders"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_sync_catalog", lang), callback_data="admin_sync"))
    
    text = (
        f"{Templates.BRAND_HEADER}\n"
        f"{I18n.t('admin_title', lang)}\n\n"
        f"{I18n.t('admin_stats', lang)}\n"
        f"{I18n.t('admin_users', lang, users=user_count)}\n"
        f"{I18n.t('admin_orders', lang, orders=total_orders)}\n"
        f"{I18n.t('admin_deposits', lang, deposits=total_deposits)}\n"
        f"{I18n.t('admin_revenue', lang, revenue=total_revenue)}\n\n"
        f"{Templates.SEPARATOR}\n"
        f"{I18n.t('admin_select_mod', lang)}"
    )
    
    if isinstance(message, types.Message):
        await message.answer(text, reply_markup=builder.as_markup())
    else:
        # Check if it was a photo message (banner)
        await update_app_screen(message.message, text, builder.as_markup(), media_path=settings.LOGO_PATH)

@router.callback_query(F.data == "admin")
async def admin_callback_root(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    await admin_panel_root(callback, state, user)

# --- SYSTEM SETTINGS ---

@router.callback_query(F.data == "admin_toggle_test")
async def toggle_test_mode(callback: types.CallbackQuery, state: FSMContext, user: User):
    if not is_admin(callback.from_user.id): return
    admin_settings.test_mode = not admin_settings.test_mode
    await callback.answer(f"Test Mode: {'ON' if admin_settings.test_mode else 'OFF'}", show_alert=True)
    await admin_panel_root(callback, state, user)

@router.callback_query(F.data == "admin_sync")
async def sync_catalog(callback: types.CallbackQuery, user: User):
    if not is_admin(callback.from_user.id): return
    await callback.answer(I18n.t("btn_sync_catalog", user.language) + "...")
    from src.core.smm.cache import service_cache
    await service_cache.refresh_cache()
    await callback.answer("✅ Catalog Synchronized", show_alert=True)

# --- USER MANAGEMENT ---

@router.callback_query(F.data == "admin_users")
async def admin_user_search_start(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    lang = user.language
    await update_app_screen(callback.message, f"{Templates.BRAND_HEADER}\n{I18n.t('admin_user_search', lang)}", InlineKeyboardBuilder().row(types.InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="admin")).as_markup(), media_path=settings.LOGO_PATH)
    await state.set_state(AdminStates.waiting_for_user_search)

@router.message(AdminStates.waiting_for_user_search)
async def admin_user_search_result(message: types.Message, state: FSMContext, user: User):
    await cleanup_input(message)
    lang = user.language
    query = message.text.replace("@", "")
    
    async with async_session() as session:
        stmt = select(User).where(or_(User.id == (int(query) if query.isdigit() else 0), User.username.ilike(f"%{query}%")))
        result = await session.execute(stmt)
        target = result.scalars().first()

    if not target:
        await message.answer(I18n.t("admin_user_not_found", lang), reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="admin")).as_markup())
        return

    await state.update_data(target_user_id=target.id)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_add_credits", lang), callback_data="admin_user_add_bal"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_rem_credits", lang), callback_data="admin_user_sub_bal"))
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_back_search", lang), callback_data="admin_users"))
    
    text = (
        f"{Templates.BRAND_HEADER}\n"
        f"{I18n.t('admin_operator_title', lang, name=target.full_name)}\n\n"
        f"• ID: <code>{target.id}</code>\n"
        f"• {I18n.t('profile_alias', lang, username=target.username or 'none')}\n"
        f"• {I18n.t('profile_rank', lang, tier=target.tier)}\n"
        f"• Balance: <b>${target.balance:.2f}</b>\n"
        f"• {I18n.t('profile_spent', lang, spent=target.total_spent)}\n"
    )
    # We send a new message for search result to not clutter the search prompt, or we update app screen.
    # Let's update app screen for consistency. 
    # But we need the original app_msg_id which we don't have easily here.
    # So we'll just send a new one with banner.
    if os.path.exists(settings.LOGO_PATH):
        await message.answer_photo(photo=types.FSInputFile(settings.LOGO_PATH), caption=text, reply_markup=builder.as_markup())
    else:
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_balance_action(callback: types.CallbackQuery, state: FSMContext, user: User):
    lang = user.language
    action_key = "add" if "add_bal" in callback.data else "sub"
    action_text = I18n.t("btn_add_credits", lang) if action_key == "add" else I18n.t("btn_rem_credits", lang)
    
    await state.update_data(bal_action=action_key)
    await callback.answer()
    await update_app_screen(callback.message, f"{Templates.BRAND_HEADER}\n{I18n.t('admin_adjust_bal', lang, action=action_text.lower())}", InlineKeyboardBuilder().row(types.InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="admin_users")).as_markup(), media_path=settings.LOGO_PATH)
    await state.set_state(AdminStates.waiting_for_balance_change)

@router.message(AdminStates.waiting_for_balance_change, F.text.regexp(r'^\d+(\.\d{1,2})?$'))
async def admin_user_balance_apply(message: types.Message, state: FSMContext, user: User):
    await cleanup_input(message)
    data = await state.get_data()
    user_id = data['target_user_id']
    action = data['bal_action']
    amount = float(message.text)
    
    async with async_session() as session:
        target = await session.get(User, user_id)
        if target:
            if action == "add":
                target.balance += amount
            else:
                target.balance = max(0, target.balance - amount)
            await session.commit()
            await message.answer(f"✅ OK: {target.full_name} | Balance: <b>${target.balance:.2f}</b>")
            await admin_panel_root(message, state, user)

# --- ORDER MANAGEMENT ---

@router.callback_query(F.data == "admin_orders")
async def admin_recent_orders(callback: types.CallbackQuery, user: User):
    await callback.answer()
    lang = user.language
    async with async_session() as session:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(10)
        result = await session.execute(stmt)
        orders = result.scalars().all()

    text = f"{Templates.BRAND_HEADER}\n{I18n.t('admin_recent_orders', lang)}\n\n"
    for o in orders:
        text += f"• <code>#{o.id}</code> | {o.status.value.upper()} | ${o.total_price:.2f} | User: {o.user_id}\n"
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="admin"))
    await update_app_screen(callback.message, text, builder.as_markup(), media_path=settings.LOGO_PATH)

# --- SETTINGS MANAGEMENT ---

@router.callback_query(F.data == "admin_set_margin")
async def admin_margin_start(callback: types.CallbackQuery, state: FSMContext, user: User):
    await callback.answer()
    lang = user.language
    await update_app_screen(callback.message, f"{Templates.BRAND_HEADER}\n{I18n.t('admin_margin_title', lang, margin=admin_settings.profit_margin)}", InlineKeyboardBuilder().row(types.InlineKeyboardButton(text=I18n.t("btn_back", lang), callback_data="admin")).as_markup(), media_path=settings.LOGO_PATH)
    await state.set_state(AdminStates.waiting_for_margin)

@router.message(AdminStates.waiting_for_margin, F.text.regexp(r'^\d+(\.\d{1,2})?$'))
async def admin_margin_apply(message: types.Message, state: FSMContext, user: User):
    await cleanup_input(message)
    new_margin = float(message.text)
    admin_settings.profit_margin = new_margin
    
    from src.core.smm.cache import service_cache
    await service_cache.refresh_cache()
    
    await message.answer(f"✅ OK: Margin {new_margin}x.")
    await admin_panel_root(message, state, user)

import os
