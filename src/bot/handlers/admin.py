from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from src.database.db import async_session
from src.database.models import Order, User, OrderStatus, Transaction, TransactionType
from src.core.config import settings
from src.bot.keyboards.inline import Keyboards
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.bot.ui.templates import Templates

router = Router()

# Global Mock Settings (In production, these would be in DB)
ADMIN_SETTINGS = {
    "test_mode": False,
    "profit_margin": settings.PROFIT_MARGIN
}

class AdminStates(StatesGroup):
    waiting_for_margin = State()
    waiting_for_rate_limit = State()

def is_admin(user_id: int):
    return user_id in settings.ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel_v2(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()

    async with async_session() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar()
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar()
        total_revenue = (await session.execute(select(func.sum(Order.total_price)).where(Order.status == OrderStatus.COMPLETED))).scalar() or 0.0
        total_deposits = (await session.execute(select(func.sum(Transaction.amount_usd)).where(Transaction.type == TransactionType.DEPOSIT))).scalar() or 0.0

    builder = InlineKeyboardBuilder()
    test_mode_text = "🟢 Test Mode: ON" if ADMIN_SETTINGS["test_mode"] else "🔴 Test Mode: OFF"
    builder.row(types.InlineKeyboardButton(text=test_mode_text, callback_data="admin_toggle_test"))
    builder.row(types.InlineKeyboardButton(text=f"📈 Margin: {ADMIN_SETTINGS['profit_margin']}x", callback_data="admin_set_margin"))
    builder.row(types.InlineKeyboardButton(text="👥 Manage Users", callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text="🎟 Support Tickets", callback_data="admin_tickets"))
    builder.row(types.InlineKeyboardButton(text="🔄 Sync Services", callback_data="admin_sync"))
    builder.row(types.InlineKeyboardButton(text="📊 View Service Stats", callback_data="admin_service_stats"))
    builder.row(types.InlineKeyboardButton(text="🔧 Configure Settings", callback_data="admin_configure"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Security Settings", callback_data="admin_security"))

    text = (
        f"{Templates.BRAND_HEADER}\n"
        "🛠 <b>TokFlare SaaS Admin Dashboard</b>\n\n"
        f"👥 <b>Total Users:</b> {user_count}\n"
        f"📦 <b>Total Orders:</b> {total_orders}\n"
        f"💰 <b>Total Deposits:</b> ${total_deposits:.2f}\n"
        f"✨ <b>Net Revenue:</b> ${total_revenue:.2f}\n\n"
        "<i>Select an option to manage the platform:</i>"
    )
    
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "admin")
async def process_admin_back(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    async with async_session() as session:
        user_count = (await session.execute(select(func.count(User.id)))).scalar()
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar()
        total_revenue = (await session.execute(select(func.sum(Order.total_price)).where(Order.status == OrderStatus.COMPLETED))).scalar() or 0.0
        total_deposits = (await session.execute(select(func.sum(Transaction.amount_usd)).where(Transaction.type == TransactionType.DEPOSIT))).scalar() or 0.0

    builder = InlineKeyboardBuilder()
    test_mode_text = "🟢 Test Mode: ON" if ADMIN_SETTINGS["test_mode"] else "🔴 Test Mode: OFF"
    builder.row(types.InlineKeyboardButton(text=test_mode_text, callback_data="admin_toggle_test"))
    builder.row(types.InlineKeyboardButton(text=f"📈 Margin: {ADMIN_SETTINGS['profit_margin']}x", callback_data="admin_set_margin"))
    builder.row(types.InlineKeyboardButton(text="👥 Manage Users", callback_data="admin_users"))
    builder.row(types.InlineKeyboardButton(text="🎟 Support Tickets", callback_data="admin_tickets"))
    builder.row(types.InlineKeyboardButton(text="🔄 Sync Services", callback_data="admin_sync"))
    builder.row(types.InlineKeyboardButton(text="📊 View Service Stats", callback_data="admin_service_stats"))
    builder.row(types.InlineKeyboardButton(text="🔧 Configure Settings", callback_data="admin_configure"))
    builder.row(types.InlineKeyboardButton(text="🛡️ Security Settings", callback_data="admin_security"))

    await callback.message.edit_text(
        f"{Templates.BRAND_HEADER}\n"
        "🛠 <b>TokFlare SaaS Admin Dashboard</b>\n\n"
        f"👥 <b>Total Users:</b> {user_count}\n"
        f"📦 <b>Total Orders:</b> {total_orders}\n"
        f"💰 <b>Total Deposits:</b> ${total_deposits:.2f}\n"
        f"✨ <b>Net Revenue:</b> ${total_revenue:.2f}\n\n"
        "<i>Select an option to manage the platform:</i>",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data == "admin_toggle_test")
async def toggle_test_mode(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    ADMIN_SETTINGS["test_mode"] = not ADMIN_SETTINGS["test_mode"]
    await callback.answer(f"Test Mode {'Enabled' if ADMIN_SETTINGS['test_mode'] else 'Disabled'}")
    await process_admin_back(callback, state)

@router.callback_query(F.data == "admin_sync")
async def admin_sync_services(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer("🔄 Syncing services...")
    from src.core.smm.cache import service_cache
    await service_cache.refresh_cache()
    await callback.answer("✅ Services Synced!", show_alert=True)
