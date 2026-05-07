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

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    tiktok_url = Column(String, nullable=False)
    comments = Column(Text, nullable=False)
    comment_count = Column(Integer)
    total_price = Column(Float)
    provider_name = Column(String, nullable=True)
    provider_cost = Column(Float, nullable=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    external_order_id = Column(String, nullable=True) # SMM Panel Order ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="orders")
    transaction = relationship("Transaction", back_populates="order", uselist=False)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    payment_id = Column(String, unique=True) # Payment Gateway ID
    amount_crypto = Column(Float)
    currency = Column(String)
    status = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="transaction")
