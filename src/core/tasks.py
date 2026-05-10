import asyncio
import logging
from sqlalchemy import select
from src.core.config import settings
from src.database.db import async_session
from src.database.models import Order, OrderStatus, Transaction, TransactionType, User
from src.core.payments.nowpayments import NOWPayments
from src.core.services.credits import CreditService
from src.bot.ui.templates import Templates

async def payment_verification_task(bot):
    """
    Background task to verify deposits and track processing orders.
    """
    nowpayments = NOWPayments()
    from src.core.smm.router import smm_router
    from src.bot.handlers.admin import ADMIN_SETTINGS
    
    while True:
        try:
            async with async_session() as session:
                # 1. Check pending DEPOSITS
                stmt = select(Transaction).where(
                    Transaction.type == TransactionType.DEPOSIT,
                    Transaction.status == "waiting"
                )
                result = await session.execute(stmt)
                pending_deposits = result.scalars().all()

                for tx in pending_deposits:
                    status = "waiting"
                    if ADMIN_SETTINGS.get("test_mode"):
                        status = "finished"
                    elif settings.NOWPAYMENTS_API_KEY and tx.payment_id:
                        status = await nowpayments.check_payment_status(tx.payment_id)
                    
                    if status == "finished":
                        bonus = CreditService.calculate_bonus(tx.amount_usd)
                        await CreditService.add_credits(
                            user_id=tx.user_id, amount=tx.amount_usd,
                            transaction_type=TransactionType.DEPOSIT,
                            session=session, bonus_amount=bonus
                        )
                        tx.status = "completed"
                        await session.commit()
                        
                        await bot.send_message(
                            tx.user_id,
                            f"{Templates.BRAND_HEADER}\n"
                            f"✨ <b>CREDITS ALLOCATED</b>\n\n"
                            f"Deposit confirmed: <b>+${tx.amount_usd:.2f}</b>\n"
                            f"Bonus incentive: <b>+${bonus:.2f}</b>\n\n"
                            f"Your secure balance has been synchronized. ⚡️"
                        )
                        
                    elif status == "failed":
                        tx.status = "failed"
                        await session.commit()
                        await bot.send_message(
                            tx.user_id,
                            f"{Templates.BRAND_HEADER}\n"
                            f"⚠️ <b>TRANSACTION FAILED</b>\n"
                            f"The gateway could not verify your deposit of ${tx.amount_usd:.2f}."
                        )

                # 2. Check processing orders
                stmt = select(Order).where(Order.status == OrderStatus.PROCESSING)
                result = await session.execute(stmt)
                orders = result.scalars().all()

                for order in orders:
                    try:
                        provider = smm_router.get_provider(order.provider_name)
                        if order.external_order_id:
                            status = await provider.get_status(order.external_order_id)
                            
                            # Log progress (only to console for now)
                            if status.value == "Completed":
                                order.status = OrderStatus.COMPLETED
                                await session.commit()
                                await bot.send_message(
                                    order.user_id,
                                    f"{Templates.BRAND_HEADER}\n"
                                    f"🏁 <b>OPERATION COMPLETE</b>\n"
                                    f"Deployment <code>#{order.id}</code> successfully finalized.\n\n"
                                    f"<i>Target: {order.tiktok_url}</i>"
                                )
                    except Exception as e:
                        logging.error(f"Error checking order #{order.id} status: {e}")

        except Exception as e:
            logging.error(f"Error in verification task: {e}")
            
        await asyncio.sleep(60)
