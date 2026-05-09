from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from src.bot.ui.templates import Templates
from src.bot.keyboards.inline import Keyboards
from src.core.smm.cache import service_cache
from src.core.services.credits import CreditService
from src.database.db import async_session
from src.database.models import Order, OrderStatus, User
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "order_new")
async def start_order_v3(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    platforms = service_cache.get_platforms()
    await callback.message.edit_text(
        f"{Templates.BRAND_HEADER}\n"
        "🌐 <b>Select Social Platform</b>\n\n"
        "Choose the network you want to boost:",
        reply_markup=Keyboards.platforms(platforms)
    )

@router.callback_query(F.data.startswith("plat_"))
async def select_action(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    platform = callback.data.split("_")[1]
    await state.update_data(platform=platform)
    actions = service_cache.get_actions(platform)
    
    builder = InlineKeyboardBuilder()
    for act in actions:
        builder.row(types.InlineKeyboardButton(text=act, callback_data=f"act_{act.split(' ')[0]}"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="order_new"))
    
    await callback.message.edit_text(
        f"{Templates.BRAND_HEADER}\n"
        f"📂 <b>{platform} Services</b>\n\n"
        "What type of interaction do you need?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("act_"))
async def select_elite_service(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    action_short = callback.data.split("_")[1]
    data = await state.get_data()
    platform = data.get('platform')
    
    # Re-find the full action name
    actions = service_cache.get_actions(platform)
    full_action = next((a for a in actions if a.startswith(action_short)), "Other")
    
    await state.update_data(action=full_action)
    services = service_cache.get_services(platform, full_action)
    
    builder = InlineKeyboardBuilder()
    for s in services:
        name = s.get('display_name')
        price = s.get('user_price_per_1000')
        builder.row(types.InlineKeyboardButton(
            text=f"{name} - ${price:.2f}", 
            callback_data=f"svc_{s.get('service')}"
        ))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data=f"plat_{platform}"))
    
    await callback.message.edit_text(
        f"{Templates.BRAND_HEADER}\n"
        f"💎 <b>Premium {full_action}</b>\n\n"
        "Select the quality tier that fits your needs.\n"
        "<i>All services are manually audited for reliability.</i>\n"
        "📊 <b>Available Services:</b>",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("svc_"))
async def order_details_v2(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    service_id = callback.data.split("_")[1]
    service = service_cache.get_service_details(service_id)
    
    display_name = service.get('display_name')
    await state.update_data(
        service_id=service_id, 
        service_name=display_name, 
        rate=service.get('user_price_per_1000'),
        min_qty=int(service.get('min', 10)),
        max_qty=int(service.get('max', 10000))
    )
    
    await callback.message.edit_text(
        f"{Templates.BRAND_HEADER}\n"
        f"📝 <b>Order Configuration</b>\n\n"
        f"🔹 Service: <b>{display_name}</b>\n"
        f"💰 Price: <b>${service.get('user_price_per_1000'):.2f} / 1000</b>\n"
        f"📦 Range: {service.get('min')} - {service.get('max')}\n"
        f"📄 Description: <i>{service.get('description', 'No description available')}</i>\n\n"
        "Please send the <b>Target URL</b> (Link):",
        reply_markup=Keyboards.cancel_order()
    )
    from src.bot.states.order import OrderStates
    await state.set_state(OrderStates.waiting_for_link)
