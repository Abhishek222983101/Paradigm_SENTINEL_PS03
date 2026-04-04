# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL DATABASE LAYER
# Financial Fraud Intelligence Platform - SQLAlchemy Models & Database Setup
# ═══════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import Optional, AsyncGenerator
import uuid
import json

from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum as SQLEnum, create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
    sessionmaker
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, async_sessionmaker
)

from .config import settings


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class FraudType:
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    CARD_TESTING = "CARD_TESTING"
    FRAUD_RING = "FRAUD_RING"
    SYNTHETIC_IDENTITY = "SYNTHETIC_IDENTITY"
    MONEY_MULE = "MONEY_MULE"
    LEGITIMATE = "LEGITIMATE"
    
    ALL = [
        ACCOUNT_TAKEOVER, CARD_TESTING, FRAUD_RING,
        SYNTHETIC_IDENTITY, MONEY_MULE, LEGITIMATE
    ]


class ActionType:
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    MFA = "MFA"
    REVIEW = "REVIEW"
    
    ALL = [ALLOW, BLOCK, MFA, REVIEW]


class AlertStatus:
    PENDING = "pending"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    
    ALL = [PENDING, INVESTIGATING, RESOLVED, DISMISSED]


# ═══════════════════════════════════════════════════════════════════════════
# BASE CLASS
# ═══════════════════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class User(Base):
    """
    User/Account model - represents a financial account holder.
    """
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    account_created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # User profile metrics (for behavioral analysis)
    avg_transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    typical_locations: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    known_devices: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")
    alerts: Mapped[list["FraudAlert"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, risk_score={self.risk_score})>"


class Transaction(Base):
    """
    Transaction model - represents a financial transaction.
    This is the core input to the ML pipeline.
    """
    __tablename__ = "transactions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    txn_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Transaction details
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    merchant: Mapped[str] = mapped_column(String(255), nullable=True)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # User reference
    user_ref_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), index=True)
    user: Mapped["User"] = relationship(back_populates="transactions")
    
    # Location & Device
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # ML Prediction Results (populated after inference)
    is_fraud: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fraud_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Explainability (SHAP values as JSON)
    shap_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Processing metrics
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Transaction(txn_id={self.txn_id}, amount={self.amount}, is_fraud={self.is_fraud})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "txn_id": self.txn_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "amount": self.amount,
            "currency": self.currency,
            "merchant": self.merchant,
            "user_id": self.user_ref_id,
            "location": self.location,
            "device_id": self.device_id,
        }
    
    def to_prediction_dict(self) -> dict:
        """Convert to prediction dictionary for API response."""
        return {
            "txn_id": self.txn_id,
            "is_fraud": self.is_fraud,
            "risk_score": self.risk_score or 0,
            "fraud_type": self.fraud_type or FraudType.LEGITIMATE,
            "action_taken": self.action_taken or ActionType.ALLOW,
            "shap_values": self.shap_values or {},
            "processing_time_ms": self.processing_time_ms or 0,
        }


class FraudAlert(Base):
    """
    Fraud Alert model - represents a flagged suspicious transaction.
    Alerts are created when risk_score > threshold.
    """
    __tablename__ = "fraud_alerts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Link to transaction
    txn_id: Mapped[str] = mapped_column(String(50), index=True)
    
    # Alert details
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    fraud_type: Mapped[str] = mapped_column(String(50), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    
    # User reference
    user_ref_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), index=True)
    user: Mapped["User"] = relationship(back_populates="alerts")
    
    # Alert status
    status: Mapped[str] = mapped_column(String(20), default=AlertStatus.PENDING)
    
    # Investigation (Mistral report as JSON)
    mistral_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    def __repr__(self) -> str:
        return f"<FraudAlert(alert_id={self.alert_id}, risk_score={self.risk_score}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.alert_id,
            "txn_id": self.txn_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "risk_score": self.risk_score,
            "fraud_type": self.fraud_type,
            "user_id": self.user_ref_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
        }


class DashboardStats(Base):
    """
    Cached dashboard statistics - updated periodically.
    """
    __tablename__ = "dashboard_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    total_fraud_detected: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    detection_rate: Mapped[float] = mapped_column(Float, default=0.0)
    false_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    blocked_amount: Mapped[float] = mapped_column(Float, default=0.0)


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE ENGINE & SESSION
# ═══════════════════════════════════════════════════════════════════════════

# For SQLite, we need aiosqlite
# For PostgreSQL, we'd use asyncpg
if "sqlite" in settings.DATABASE_URL:
    # SQLite requires special handling
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    Use with FastAPI's Depends().
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """
    Drop all tables - use with caution!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
