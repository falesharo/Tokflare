import logging
from sqlalchemy import select
from src.database.models import User, Transaction, TransactionType
from src.database.db import async_session

logger = logging.getLogger(__name__)

class CreditService:
    @staticmethod
    async def add_credits(user_id: int, amount: float, transaction_type: TransactionType, session, order_id=None, bonus_amount=0.0, payment_id=None, currency=None):
        """Adds credits to a user balance and logs the transaction."""
        user = await session.get(User, user_id)
        if not user:
            return False
        
        user.balance += (amount + bonus_amount)
        
        transaction = Transaction(
            user_id=user_id,
            order_id=order_id,
            type=transaction_type,
            amount_usd=amount,
            bonus_amount=bonus_amount,
            payment_id=payment_id,
            currency=currency,
            status="completed"
        )
        session.add(transaction)
        
        # Referral Commission (if applicable)
        if transaction_type == TransactionType.DEPOSIT and user.referrer_id:
            commission = amount * 0.05 # 5% Referral bonus
            referrer = await session.get(User, user.referrer_id)
            if referrer:
                referrer.balance += commission
                ref_transaction = Transaction(
                    user_id=user.referrer_id,
                    type=TransactionType.REFERRAL_BONUS,
                    amount_usd=commission,
                    status="completed"
                )
                session.add(ref_transaction)
                logger.info(f"Referral commission of ${commission} paid to {user.referrer_id}")

        await session.commit()
        return True

    @staticmethod
    async def deduct_credits(user_id: int, amount: float, session, order_id=None):
        """Deducts credits from user balance."""
        user = await session.get(User, user_id)
        if not user or user.balance < amount:
            return False
        
        user.balance -= amount
        
        transaction = Transaction(
            user_id=user_id,
            order_id=order_id,
            type=TransactionType.ORDER_PAYMENT,
            amount_usd=amount,
            status="completed"
        )
        session.add(transaction)
        await session.commit()
        return True

    @staticmethod
    def calculate_bonus(amount: float) -> float:
        """Calculates recharge bonus based on amount tiers."""
        if amount >= 200:
            return amount * 0.15
        elif amount >= 100:
            return amount * 0.10
        elif amount >= 50:
            return amount * 0.05
        return 0.0
