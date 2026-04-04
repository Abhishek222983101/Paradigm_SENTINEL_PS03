# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL API SCHEMAS
# Financial Fraud Intelligence Platform - Pydantic Models for API Validation
# ═══════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS (Matching Frontend Types)
# ═══════════════════════════════════════════════════════════════════════════

class FraudTypeEnum(str, Enum):
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    CARD_TESTING = "CARD_TESTING"
    FRAUD_RING = "FRAUD_RING"
    SYNTHETIC_IDENTITY = "SYNTHETIC_IDENTITY"
    MONEY_MULE = "MONEY_MULE"
    LEGITIMATE = "LEGITIMATE"


class ActionTypeEnum(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    MFA = "MFA"
    REVIEW = "REVIEW"


class AlertStatusEnum(str, Enum):
    pending = "pending"
    investigating = "investigating"
    resolved = "resolved"
    dismissed = "dismissed"


class RiskLevelEnum(str, Enum):
    safe = "safe"
    warning = "warning"
    critical = "critical"


class AttackScenarioEnum(str, Enum):
    normal = "normal"
    account_takeover = "account_takeover"
    card_testing = "card_testing"
    fraud_ring = "fraud_ring"
    synthetic_identity = "synthetic_identity"


# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTION SCHEMAS (Integration Contract)
# ═══════════════════════════════════════════════════════════════════════════

class TransactionBase(BaseModel):
    """Base transaction schema - input from payment gateway."""
    txn_id: str = Field(..., description="Unique transaction identifier")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    amount: float = Field(..., ge=0, description="Transaction amount")
    currency: str = Field(default="USD", max_length=10)
    merchant: str = Field(..., description="Merchant name")
    user_id: str = Field(..., description="User/Account identifier")
    location: str = Field(..., description="Transaction location")
    device_id: str = Field(..., description="Device fingerprint")


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass


class TransactionResponse(TransactionBase):
    """Schema for transaction response (without prediction)."""
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════
# PREDICTION SCHEMAS (Integration Contract)
# ═══════════════════════════════════════════════════════════════════════════

class PredictionBase(BaseModel):
    """ML Prediction result schema."""
    txn_id: str
    is_fraud: bool
    risk_score: float = Field(..., ge=0, le=100)
    fraud_type: FraudTypeEnum
    action_taken: ActionTypeEnum
    shap_values: Dict[str, float] = Field(default_factory=dict)
    processing_time_ms: float = Field(..., ge=0)


class PredictionResponse(PredictionBase):
    """Schema for prediction response."""
    model_config = ConfigDict(from_attributes=True)


class TransactionWithPrediction(TransactionBase):
    """Combined transaction with prediction."""
    prediction: Optional[PredictionResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


# ═══════════════════════════════════════════════════════════════════════════
# ALERT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class FraudAlertBase(BaseModel):
    """Base fraud alert schema."""
    id: str
    txn_id: str
    timestamp: str
    risk_score: float
    fraud_type: FraudTypeEnum
    user_id: str
    amount: float
    currency: str
    status: AlertStatusEnum


class FraudAlertResponse(FraudAlertBase):
    """Schema for alert response."""
    model_config = ConfigDict(from_attributes=True)


class FraudAlertUpdate(BaseModel):
    """Schema for updating an alert."""
    status: Optional[AlertStatusEnum] = None
    analyst_notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD STATS SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class DashboardStatsResponse(BaseModel):
    """Dashboard statistics overview."""
    total_transactions: int
    total_fraud_detected: int
    avg_latency_ms: float
    detection_rate: float
    false_positive_rate: float
    blocked_amount: float


# ═══════════════════════════════════════════════════════════════════════════
# INVESTIGATION REPORT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class ShapValueSchema(BaseModel):
    """SHAP value entry for explainability."""
    feature: str
    value: float
    impact: Literal["positive", "negative"]


class InvestigationReportSchema(BaseModel):
    """Investigation report from Mistral LLM."""
    txn_id: str
    summary: str
    evidence: List[str]
    recommendations: List[str]
    similar_cases: List[str]
    confidence: float
    generated_at: str


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH VISUALIZATION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class GraphNodeSchema(BaseModel):
    """Graph node for Cytoscape visualization."""
    id: str
    type: Literal["user", "device", "ip", "card", "merchant"]
    label: str
    risk_score: Optional[float] = None
    is_fraud: Optional[bool] = None


class GraphEdgeSchema(BaseModel):
    """Graph edge for Cytoscape visualization."""
    id: str
    source: str
    target: str
    type: Literal["transaction", "shared_device", "shared_ip", "transfer"]
    weight: Optional[float] = None


class GraphDataSchema(BaseModel):
    """Complete graph data structure."""
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class SimulatorStateSchema(BaseModel):
    """Simulator control state."""
    isRunning: bool
    scenario: AttackScenarioEnum
    transactionsPerSecond: float = Field(default=2.5, ge=0.1, le=100)
    attackIntensity: Literal["low", "medium", "high"]


class SimulatorInjectRequest(BaseModel):
    """Request to inject an attack scenario."""
    scenario: AttackScenarioEnum
    intensity: Literal["low", "medium", "high"] = "medium"
    duration_seconds: int = Field(default=10, ge=1, le=60)


# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET MESSAGE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class WebSocketMessageSchema(BaseModel):
    """WebSocket message structure."""
    type: Literal["transaction", "alert", "stats_update", "system_status"]
    payload: Any
    timestamp: str


# ═══════════════════════════════════════════════════════════════════════════
# API RESPONSE WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    limit: int
    pages: int


class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Optional[PaginationMeta] = None
