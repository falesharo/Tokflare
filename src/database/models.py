from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, BigInteger, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class OrderStatus(enum.Enum):
    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    ORDER_PAYMENT = "order_payment"
    REFERRAL_BONUS = "referral_bonus"

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    full_name = Column(String)
    balance = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    tier = Column(String, default="BRONZE") # BRONZE, SILVER, GOLD, ELITE
    language = Column(String, default="en") # en, fr
    is_admin = Column(BigInteger, default=0) 
    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    tiktok_url = Column(String, nullable=False)
    service_id = Column(String, nullable=True) # SMM Service ID
    category = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    comment_count = Column(Integer)
    total_price = Column(Float)
    provider_name = Column(String, nullable=True)
    provider_cost = Column(Float, nullable=True)
    
    # Drip-feed fields
    is_drip_feed = Column(BigInteger, default=0) # 0 or 1
    runs = Column(Integer, nullable=True)
    interval = Column(Integer, nullable=True)
    
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    external_order_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")
    transaction = relationship("Transaction", back_populates="order", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    type = Column(Enum(TransactionType))
    payment_id = Column(String, unique=True, nullable=True)
    amount_usd = Column(Float)
    amount_crypto = Column(Float, nullable=True)
    bonus_amount = Column(Float, default=0.0)
    currency = Column(String, nullable=True)
    status = Column(String)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
    order = relationship("Order", back_populates="transaction")

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    subject = Column(String)
    message = Column(Text)
    status = Column(String, default="open") # open, closed, replied
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
