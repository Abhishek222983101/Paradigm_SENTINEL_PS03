# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL WEBSOCKET HANDLER
# Financial Fraud Intelligence Platform - Real-Time Transaction Streaming
# ═══════════════════════════════════════════════════════════════════════════

import asyncio
import json
from datetime import datetime
from typing import Set, Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from utils.config import settings
from utils.mock_data import (
    generate_transaction,
    generate_alert_from_transaction,
    inject_attack_scenario,
)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTER INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

router = APIRouter(tags=["WebSocket"])


# ═══════════════════════════════════════════════════════════════════════════
# CONNECTION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    """
    Manages WebSocket connections for real-time transaction streaming.
    
    Supports multiple channels:
    - transactions: Real-time transaction feed
    - alerts: High-risk fraud alerts
    - stats: Dashboard statistics updates
    """
    
    def __init__(self):
        # Active connections per channel
        self.connections: Dict[str, Set[WebSocket]] = {
            "transactions": set(),
            "alerts": set(),
            "stats": set(),
            "all": set(),  # Receives all message types
        }
        # Streaming state
        self.is_streaming = False
        self.stream_task: Optional[asyncio.Task] = None
        # Attack injection state
        self.attack_active = False
        self.attack_scenario: Optional[str] = None
    
    async def connect(self, websocket: WebSocket, channel: str = "all"):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if channel not in self.connections:
            channel = "all"
        
        self.connections[channel].add(websocket)
        print(f"[WS] Client connected to channel: {channel}")
        
        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "system_status",
                "payload": {
                    "status": "connected",
                    "channel": channel,
                    "message": f"Welcome to SENTINEL {channel} stream",
                    "streaming": self.is_streaming,
                },
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
        
        # Start streaming if this is the first connection
        if not self.is_streaming:
            await self.start_streaming()
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        for channel in self.connections.values():
            channel.discard(websocket)
        print("[WS] Client disconnected")
        
        # Stop streaming if no more connections
        total_connections = sum(len(c) for c in self.connections.values())
        if total_connections == 0 and self.is_streaming:
            self.stop_streaming()
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[WS] Error sending message: {e}")
    
    async def broadcast(self, message: dict, channel: str = "all"):
        """Broadcast a message to all clients in a channel."""
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat() + "Z"
        
        # Get target connections
        targets = set()
        if channel in self.connections:
            targets.update(self.connections[channel])
        # Always include "all" channel
        targets.update(self.connections["all"])
        
        # Remove duplicates
        disconnected = set()
        
        for websocket in targets:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"[WS] Broadcast error: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def start_streaming(self):
        """Start the mock transaction streaming task."""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stream_task = asyncio.create_task(self._stream_transactions())
        print("[WS] Transaction streaming started")
    
    def stop_streaming(self):
        """Stop the transaction streaming task."""
        self.is_streaming = False
        if self.stream_task:
            self.stream_task.cancel()
        print("[WS] Transaction streaming stopped")
    
    async def _stream_transactions(self):
        """
        Background task that generates and broadcasts mock transactions.
        Runs continuously while clients are connected.
        """
        try:
            while self.is_streaming:
                # Generate transaction
                if self.attack_active and self.attack_scenario:
                    # Generate attack transactions
                    txns, alerts = inject_attack_scenario(
                        self.attack_scenario,
                        intensity="high"
                    )
                    for txn in txns:
                        await self._broadcast_transaction(txn)
                        if alerts:
                            await self._broadcast_alert(alerts[0])
                        await asyncio.sleep(0.2)  # Fast during attack
                else:
                    # Normal flow
                    txn = generate_transaction()
                    await self._broadcast_transaction(txn)
                    
                    # Generate alert if high risk
                    if txn.get("risk_score", 0) >= 80:
                        alert = generate_alert_from_transaction(txn)
                        await self._broadcast_alert(alert)
                
                # Sleep based on configured rate
                interval = 1.0 / settings.WS_TRANSACTION_RATE
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            print("[WS] Transaction stream cancelled")
        except Exception as e:
            print(f"[WS] Stream error: {e}")
            self.is_streaming = False
    
    async def _broadcast_transaction(self, txn: dict):
        """Broadcast a transaction message."""
        message = {
            "type": "transaction",
            "payload": {
                "txn_id": txn["txn_id"],
                "timestamp": txn["timestamp"],
                "amount": txn["amount"],
                "currency": txn["currency"],
                "merchant": txn["merchant"],
                "user_id": txn["user_id"],
                "location": txn["location"],
                "device_id": txn["device_id"],
                "prediction": {
                    "is_fraud": txn["is_fraud"],
                    "risk_score": txn["risk_score"],
                    "fraud_type": txn["fraud_type"],
                    "action_taken": txn["action_taken"],
                    "shap_values": txn["shap_values"],
                    "processing_time_ms": txn["processing_time_ms"]
                }
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        await self.broadcast(message, channel="transactions")
    
    async def _broadcast_alert(self, alert: dict):
        """Broadcast an alert message."""
        message = {
            "type": "alert",
            "payload": alert,
            "timestamp": datetime.now().isoformat() + "Z"
        }
        await self.broadcast(message, channel="alerts")
    
    async def inject_attack(self, scenario: str, duration_seconds: int = 10):
        """
        Inject an attack scenario for a specified duration.
        """
        self.attack_active = True
        self.attack_scenario = scenario
        
        # Notify clients
        await self.broadcast({
            "type": "system_status",
            "payload": {
                "status": "attack_started",
                "scenario": scenario,
                "duration": duration_seconds,
                "message": f"⚠️ ATTACK DETECTED: {scenario.upper().replace('_', ' ')}"
            }
        })
        
        # Auto-disable after duration
        await asyncio.sleep(duration_seconds)
        
        self.attack_active = False
        self.attack_scenario = None
        
        await self.broadcast({
            "type": "system_status",
            "payload": {
                "status": "attack_ended",
                "message": "Attack simulation completed"
            }
        })


# Global connection manager instance
manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.websocket("/ws/transactions")
async def websocket_transactions(websocket: WebSocket):
    """
    WebSocket endpoint for real-time transaction stream.
    
    Messages sent:
    - type: "transaction" - New transaction with prediction
    - type: "alert" - High-risk fraud alert
    - type: "system_status" - System status updates
    """
    await manager.connect(websocket, channel="transactions")
    
    try:
        while True:
            # Keep connection alive and handle incoming commands
            data = await websocket.receive_text()
            
            try:
                command = json.loads(data)
                await handle_command(websocket, command)
            except json.JSONDecodeError:
                print(f"[WS] Invalid JSON: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for fraud alert stream only.
    """
    await manager.connect(websocket, channel="alerts")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                await handle_command(websocket, command)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/all")
async def websocket_all(websocket: WebSocket):
    """
    WebSocket endpoint that receives all message types.
    """
    await manager.connect(websocket, channel="all")
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                await handle_command(websocket, command)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_command(websocket: WebSocket, command: dict):
    """
    Handle incoming WebSocket commands from clients.
    
    Commands:
    - ping: Heartbeat check
    - inject_attack: Trigger attack scenario
    - stop_attack: Stop current attack
    - get_stats: Request current stats
    """
    cmd_type = command.get("type", "")
    
    if cmd_type == "ping":
        await manager.send_personal_message(websocket, {
            "type": "pong",
            "payload": {"status": "alive"},
            "timestamp": datetime.now().isoformat() + "Z"
        })
    
    elif cmd_type == "inject_attack":
        scenario = command.get("scenario", "account_takeover")
        duration = command.get("duration", 10)
        # Run attack in background
        asyncio.create_task(manager.inject_attack(scenario, duration))
    
    elif cmd_type == "stop_attack":
        manager.attack_active = False
        manager.attack_scenario = None
        await manager.broadcast({
            "type": "system_status",
            "payload": {
                "status": "attack_stopped",
                "message": "Attack manually stopped"
            }
        })
    
    elif cmd_type == "get_stats":
        # Send current stats
        from api.routes import _transactions_store, _alerts_store
        
        total_txns = len(_transactions_store)
        fraud_txns = len([t for t in _transactions_store if t.get("is_fraud", False)])
        
        await manager.send_personal_message(websocket, {
            "type": "stats_update",
            "payload": {
                "total_transactions": total_txns,
                "total_fraud_detected": fraud_txns,
                "active_alerts": len([a for a in _alerts_store if a.get("status") == "pending"]),
                "streaming": manager.is_streaming,
                "attack_active": manager.attack_active
            },
            "timestamp": datetime.now().isoformat() + "Z"
        })
