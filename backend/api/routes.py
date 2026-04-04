# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL API ROUTES
# Financial Fraud Intelligence Platform - REST API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ApiResponse,
    TransactionResponse,
    TransactionWithPrediction,
    PredictionResponse,
    FraudAlertResponse,
    FraudAlertUpdate,
    DashboardStatsResponse,
    InvestigationReportSchema,
    GraphDataSchema,
    SimulatorInjectRequest,
)
from utils.config import settings
from utils.mock_data import (
    generate_transaction,
    generate_transactions_batch,
    generate_alert_from_transaction,
    generate_dashboard_stats,
    inject_attack_scenario,
    generate_fraud_ring_graph,
    generate_mock_investigation_report,
)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTER INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/v1", tags=["SENTINEL API"])


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (For Mock Mode)
# In production, these would be database queries
# ═══════════════════════════════════════════════════════════════════════════

# Initialize mock data stores
_transactions_store: List[dict] = []
_alerts_store: List[dict] = []
_stats_store: dict = generate_dashboard_stats()

# Pre-populate with some transactions
def _init_mock_data():
    global _transactions_store, _alerts_store
    if not _transactions_store:
        _transactions_store = generate_transactions_batch(100, fraud_ratio=0.08)
        _alerts_store = [
            generate_alert_from_transaction(txn)
            for txn in _transactions_store
            if txn.get("risk_score", 0) >= 70
        ]

_init_mock_data()


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "operational",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode": "mock" if settings.USE_MOCK_ML else "production",
        "timestamp": datetime.now().isoformat() + "Z"
    }


# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/transactions/recent", response_model=ApiResponse)
async def get_recent_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    fraud_only: bool = Query(default=False),
):
    """
    Get recent transactions with optional fraud filter.
    """
    # Filter transactions
    filtered = _transactions_store
    if fraud_only:
        filtered = [t for t in filtered if t.get("is_fraud", False)]
    
    # Sort by timestamp (most recent first)
    sorted_txns = sorted(
        filtered,
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )
    
    # Paginate
    paginated = sorted_txns[offset:offset + limit]
    
    return ApiResponse(
        success=True,
        data=paginated,
        meta={
            "total": len(filtered),
            "page": offset // limit + 1,
            "limit": limit,
            "pages": (len(filtered) + limit - 1) // limit
        }
    )


@router.get("/transactions/{txn_id}", response_model=ApiResponse)
async def get_transaction(txn_id: str):
    """
    Get a specific transaction by ID.
    """
    for txn in _transactions_store:
        if txn.get("txn_id") == txn_id:
            return ApiResponse(success=True, data=txn)
    
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")


@router.post("/transactions/predict", response_model=ApiResponse)
async def predict_transaction(transaction: dict):
    """
    Submit a transaction for fraud prediction.
    In mock mode, this generates a fake prediction.
    In production mode, this would call the ML pipeline.
    """
    if settings.USE_MOCK_ML:
        # Generate mock prediction
        txn = generate_transaction()
        # Merge with incoming data
        txn.update({
            "txn_id": transaction.get("txn_id", txn["txn_id"]),
            "amount": transaction.get("amount", txn["amount"]),
            "merchant": transaction.get("merchant", txn["merchant"]),
            "user_id": transaction.get("user_id", txn["user_id"]),
            "location": transaction.get("location", txn["location"]),
        })
        
        _transactions_store.insert(0, txn)
        
        # Create alert if high risk
        if txn.get("risk_score", 0) >= 70:
            alert = generate_alert_from_transaction(txn)
            _alerts_store.insert(0, alert)
        
        return ApiResponse(
            success=True,
            data={
                "transaction": txn,
                "prediction": {
                    "txn_id": txn["txn_id"],
                    "is_fraud": txn["is_fraud"],
                    "risk_score": txn["risk_score"],
                    "fraud_type": txn["fraud_type"],
                    "action_taken": txn["action_taken"],
                    "shap_values": txn["shap_values"],
                    "processing_time_ms": txn["processing_time_ms"]
                }
            }
        )
    else:
        # TODO: Call actual ML pipeline
        raise HTTPException(
            status_code=501,
            detail="Production ML mode not yet implemented"
        )


# ═══════════════════════════════════════════════════════════════════════════
# ALERT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/alerts/active", response_model=ApiResponse)
async def get_active_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
):
    """
    Get active fraud alerts.
    """
    filtered = _alerts_store
    
    if status:
        filtered = [a for a in filtered if a.get("status") == status]
    
    # Sort by risk score (highest first)
    sorted_alerts = sorted(
        filtered,
        key=lambda x: x.get("risk_score", 0),
        reverse=True
    )[:limit]
    
    return ApiResponse(
        success=True,
        data=sorted_alerts,
        meta={
            "total": len(filtered),
            "page": 1,
            "limit": limit,
            "pages": 1
        }
    )


@router.get("/alerts/{alert_id}", response_model=ApiResponse)
async def get_alert(alert_id: str):
    """
    Get a specific alert by ID.
    """
    for alert in _alerts_store:
        if alert.get("id") == alert_id:
            return ApiResponse(success=True, data=alert)
    
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@router.patch("/alerts/{alert_id}", response_model=ApiResponse)
async def update_alert(alert_id: str, update: FraudAlertUpdate):
    """
    Update an alert's status or notes.
    """
    for alert in _alerts_store:
        if alert.get("id") == alert_id:
            if update.status:
                alert["status"] = update.status
            if update.analyst_notes:
                alert["analyst_notes"] = update.analyst_notes
            return ApiResponse(success=True, data=alert)
    
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD STATS ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/stats/overview")
async def get_dashboard_stats():
    """
    Get dashboard overview statistics.
    """
    # Calculate live stats from mock data
    total_txns = len(_transactions_store)
    fraud_txns = len([t for t in _transactions_store if t.get("is_fraud", False)])
    blocked_amount = sum(
        t.get("amount", 0)
        for t in _transactions_store
        if t.get("action_taken") == "BLOCK"
    )
    avg_latency = sum(
        t.get("processing_time_ms", 0)
        for t in _transactions_store
    ) / max(1, total_txns)
    
    stats = {
        "total_transactions": total_txns,
        "total_fraud_detected": fraud_txns,
        "avg_latency_ms": round(avg_latency, 1),
        "detection_rate": round((fraud_txns / max(1, total_txns)) * 100, 2),
        "false_positive_rate": round(2.3, 2),  # Mock value
        "blocked_amount": round(blocked_amount, 2)
    }
    
    return ApiResponse(success=True, data=stats)


# ═══════════════════════════════════════════════════════════════════════════
# INVESTIGATION / EXPLAINABILITY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/investigate/{txn_id}")
async def investigate_transaction(txn_id: str):
    """
    Get detailed investigation report for a transaction.
    Uses Mistral LLM in production, mock data otherwise.
    """
    # Find the transaction
    txn = None
    for t in _transactions_store:
        if t.get("txn_id") == txn_id:
            txn = t
            break
    
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")
    
    # Generate investigation report
    report = generate_mock_investigation_report(txn)
    
    return ApiResponse(
        success=True,
        data={
            "transaction": txn,
            "report": report
        }
    )


@router.get("/explain/{txn_id}")
async def explain_prediction(txn_id: str):
    """
    Get SHAP explanation for a prediction.
    """
    for txn in _transactions_store:
        if txn.get("txn_id") == txn_id:
            shap_values = txn.get("shap_values", {})
            
            # Format SHAP values as list with impact direction
            formatted_shap = [
                {
                    "feature": feature,
                    "value": value,
                    "impact": "positive" if value > 0 else "negative"
                }
                for feature, value in sorted(
                    shap_values.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )
            ]
            
            return ApiResponse(
                success=True,
                data={
                    "txn_id": txn_id,
                    "risk_score": txn.get("risk_score", 0),
                    "fraud_type": txn.get("fraud_type", "LEGITIMATE"),
                    "shap_values": formatted_shap
                }
            )
    
    raise HTTPException(status_code=404, detail=f"Transaction {txn_id} not found")


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH VISUALIZATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/graph/ring/{user_id}")
async def get_fraud_ring_graph(user_id: str):
    """
    Get graph data for fraud ring visualization.
    """
    # Generate mock fraud ring graph
    graph_data = generate_fraud_ring_graph(ring_size=5)
    
    return ApiResponse(success=True, data=graph_data)


@router.get("/graph/network")
async def get_network_graph(
    limit: int = Query(default=50, ge=10, le=200),
):
    """
    Get general network graph of recent transactions.
    """
    # Build graph from recent transactions
    nodes = []
    edges = []
    seen_users = set()
    seen_devices = set()
    
    for txn in _transactions_store[:limit]:
        user_id = txn.get("user_id")
        device_id = txn.get("device_id")
        
        # Add user node
        if user_id and user_id not in seen_users:
            nodes.append({
                "id": user_id,
                "type": "user",
                "label": user_id,
                "risk_score": txn.get("risk_score", 0),
                "is_fraud": txn.get("is_fraud", False)
            })
            seen_users.add(user_id)
        
        # Add device node
        if device_id and device_id not in seen_devices:
            nodes.append({
                "id": device_id,
                "type": "device",
                "label": device_id,
                "risk_score": txn.get("risk_score", 0) * 0.8,
                "is_fraud": txn.get("is_fraud", False)
            })
            seen_devices.add(device_id)
        
        # Add edge
        if user_id and device_id:
            edges.append({
                "id": f"edge-{txn.get('txn_id')}",
                "source": user_id,
                "target": device_id,
                "type": "transaction",
                "weight": txn.get("amount", 0)
            })
    
    return ApiResponse(
        success=True,
        data={"nodes": nodes, "edges": edges}
    )


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/simulator/inject", response_model=ApiResponse)
async def inject_attack(request: SimulatorInjectRequest, background_tasks: BackgroundTasks):
    """
    Inject an attack scenario into the transaction stream.
    """
    # Generate attack transactions
    transactions, alerts = inject_attack_scenario(
        scenario=request.scenario.value,
        intensity=request.intensity
    )
    
    # Add to stores
    _transactions_store[:0] = transactions  # Prepend to store
    _alerts_store[:0] = alerts
    
    return ApiResponse(
        success=True,
        data={
            "scenario": request.scenario.value,
            "intensity": request.intensity,
            "transactions_generated": len(transactions),
            "alerts_generated": len(alerts),
            "message": f"Successfully injected {request.scenario.value} attack"
        }
    )


@router.post("/simulator/reset", response_model=ApiResponse)
async def reset_simulator():
    """
    Reset simulator to clean state with fresh mock data.
    """
    global _transactions_store, _alerts_store, _stats_store
    
    _transactions_store = generate_transactions_batch(100, fraud_ratio=0.08)
    _alerts_store = [
        generate_alert_from_transaction(txn)
        for txn in _transactions_store
        if txn.get("risk_score", 0) >= 70
    ]
    _stats_store = generate_dashboard_stats()
    
    return ApiResponse(
        success=True,
        data={"message": "Simulator reset to clean state"}
    )


# ═══════════════════════════════════════════════════════════════════════════
# BATCH ENDPOINTS (For Testing)
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/batch/generate", response_model=ApiResponse)
async def generate_batch(
    count: int = Query(default=50, ge=1, le=500),
    fraud_ratio: float = Query(default=0.05, ge=0, le=1),
):
    """
    Generate a batch of mock transactions.
    """
    batch = generate_transactions_batch(count, fraud_ratio)
    _transactions_store[:0] = batch
    
    # Generate alerts for high-risk transactions
    new_alerts = [
        generate_alert_from_transaction(txn)
        for txn in batch
        if txn.get("risk_score", 0) >= 70
    ]
    _alerts_store[:0] = new_alerts
    
    return ApiResponse(
        success=True,
        data={
            "transactions_generated": len(batch),
            "alerts_generated": len(new_alerts)
        }
    )
