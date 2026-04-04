// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL WEBSOCKET HOOKS
// Real-time Transaction & Alert Streaming
// ═══════════════════════════════════════════════════════════════════════════

"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type {
  TransactionWithPrediction,
  FraudAlert,
  WebSocketMessage,
  DashboardStats,
} from "@/types";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface UseTransactionStreamOptions {
  /** WebSocket URL (default: ws://localhost:8000/ws/transactions) */
  url?: string;
  /** Maximum transactions to keep in memory */
  maxTransactions?: number;
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean;
  /** Reconnect delay in ms (uses exponential backoff) */
  reconnectDelay?: number;
  /** Maximum reconnect attempts */
  maxReconnectAttempts?: number;
  /** Callback when new transaction arrives */
  onTransaction?: (txn: TransactionWithPrediction) => void;
  /** Callback when new alert arrives */
  onAlert?: (alert: FraudAlert) => void;
}

interface TransactionStreamState {
  /** Array of recent transactions */
  transactions: TransactionWithPrediction[];
  /** Array of active alerts */
  alerts: FraudAlert[];
  /** Whether connected to WebSocket */
  isConnected: boolean;
  /** Whether currently reconnecting */
  isReconnecting: boolean;
  /** Connection error message */
  error: string | null;
  /** Current attack scenario (if active) */
  attackActive: string | null;
  /** Last received stats update */
  stats: Partial<DashboardStats> | null;
}

interface UseTransactionStreamReturn extends TransactionStreamState {
  /** Manually connect to WebSocket */
  connect: () => void;
  /** Manually disconnect from WebSocket */
  disconnect: () => void;
  /** Inject an attack scenario */
  injectAttack: (scenario: string, duration?: number) => void;
  /** Stop current attack */
  stopAttack: () => void;
  /** Request current stats */
  requestStats: () => void;
  /** Clear all transactions */
  clearTransactions: () => void;
}

// ═══════════════════════════════════════════════════════════════════════════
// HOOK IMPLEMENTATION
// ═══════════════════════════════════════════════════════════════════════════

export function useTransactionStream(
  options: UseTransactionStreamOptions = {}
): UseTransactionStreamReturn {
  const {
    url = "ws://localhost:8000/ws/transactions",
    maxTransactions = 50,
    autoReconnect = true,
    reconnectDelay = 1000,
    maxReconnectAttempts = 10,
    onTransaction,
    onAlert,
  } = options;

  // State
  const [state, setState] = useState<TransactionStreamState>({
    transactions: [],
    alerts: [],
    isConnected: false,
    isReconnecting: false,
    error: null,
    attackActive: null,
    stats: null,
  });

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(autoReconnect);

  // ─────────────────────────────────────────────────────────────────────────
  // WEBSOCKET CONNECTION
  // ─────────────────────────────────────────────────────────────────────────

  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setState((prev) => ({
          ...prev,
          isConnected: true,
          isReconnecting: false,
          error: null,
        }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (err) {
          // Silently ignore parse errors for malformed messages
        }
      };

      ws.onerror = (_error) => {
        setState((prev) => ({
          ...prev,
          error: "Connection error",
        }));
      };

      ws.onclose = (event) => {
        wsRef.current = null;
        setState((prev) => ({
          ...prev,
          isConnected: false,
        }));

        // Auto-reconnect with exponential backoff
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          
          setState((prev) => ({ ...prev, isReconnecting: true }));
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: "Failed to connect",
        isConnected: false,
      }));
    }
  }, [url, reconnectDelay, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setState((prev) => ({
      ...prev,
      isConnected: false,
      isReconnecting: false,
    }));
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // MESSAGE HANDLING
  // ─────────────────────────────────────────────────────────────────────────

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      switch (message.type) {
        case "transaction": {
          const payload = message.payload as {
            txn_id: string;
            timestamp: string;
            amount: number;
            currency: string;
            merchant: string;
            user_id: string;
            location: string;
            device_id: string;
            prediction: {
              is_fraud: boolean;
              risk_score: number;
              fraud_type: string;
              action_taken: string;
              shap_values: Record<string, number>;
              processing_time_ms: number;
            };
          };

          const txn: TransactionWithPrediction = {
            txn_id: payload.txn_id,
            timestamp: payload.timestamp,
            amount: payload.amount,
            currency: payload.currency,
            merchant: payload.merchant,
            user_id: payload.user_id,
            location: payload.location,
            device_id: payload.device_id,
            prediction: {
              txn_id: payload.txn_id,
              is_fraud: payload.prediction.is_fraud,
              risk_score: payload.prediction.risk_score,
              fraud_type: payload.prediction.fraud_type as TransactionWithPrediction["prediction"] extends { fraud_type: infer T } ? T : never,
              action_taken: payload.prediction.action_taken as TransactionWithPrediction["prediction"] extends { action_taken: infer T } ? T : never,
              shap_values: payload.prediction.shap_values,
              processing_time_ms: payload.prediction.processing_time_ms,
            },
          };

          setState((prev) => ({
            ...prev,
            transactions: [txn, ...prev.transactions].slice(0, maxTransactions),
          }));

          onTransaction?.(txn);
          break;
        }

        case "alert": {
          const alert = message.payload as FraudAlert;
          
          setState((prev) => ({
            ...prev,
            alerts: [alert, ...prev.alerts.filter((a) => a.id !== alert.id)].slice(0, 20),
          }));

          onAlert?.(alert);
          break;
        }

        case "stats_update": {
          const stats = message.payload as Partial<DashboardStats>;
          setState((prev) => ({
            ...prev,
            stats,
          }));
          break;
        }

        case "system_status": {
          const status = message.payload as {
            status: string;
            scenario?: string;
            message?: string;
          };

          if (status.status === "attack_started") {
            setState((prev) => ({
              ...prev,
              attackActive: status.scenario || null,
            }));
          } else if (status.status === "attack_ended" || status.status === "attack_stopped") {
            setState((prev) => ({
              ...prev,
              attackActive: null,
            }));
          }
          break;
        }
      }
    },
    [maxTransactions, onTransaction, onAlert]
  );

  // ─────────────────────────────────────────────────────────────────────────
  // COMMANDS
  // ─────────────────────────────────────────────────────────────────────────

  const sendCommand = useCallback((command: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(command));
    }
  }, []);

  const injectAttack = useCallback(
    (scenario: string, duration: number = 10) => {
      sendCommand({
        type: "inject_attack",
        scenario,
        duration,
      });
    },
    [sendCommand]
  );

  const stopAttack = useCallback(() => {
    sendCommand({ type: "stop_attack" });
  }, [sendCommand]);

  const requestStats = useCallback(() => {
    sendCommand({ type: "get_stats" });
  }, [sendCommand]);

  const clearTransactions = useCallback(() => {
    setState((prev) => ({
      ...prev,
      transactions: [],
    }));
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // LIFECYCLE
  // ─────────────────────────────────────────────────────────────────────────

  useEffect(() => {
    shouldReconnectRef.current = autoReconnect;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect, autoReconnect]);

  // ─────────────────────────────────────────────────────────────────────────
  // RETURN
  // ─────────────────────────────────────────────────────────────────────────

  return {
    ...state,
    connect,
    disconnect,
    injectAttack,
    stopAttack,
    requestStats,
    clearTransactions,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// SIMPLE ALERT STREAM HOOK
// For components that only need alerts
// ═══════════════════════════════════════════════════════════════════════════

export function useAlertStream(options: { url?: string; maxAlerts?: number } = {}) {
  const { url = "ws://localhost:8000/ws/alerts", maxAlerts = 20 } = options;

  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        if (message.type === "alert") {
          const alert = message.payload as FraudAlert;
          setAlerts((prev) => [alert, ...prev].slice(0, maxAlerts));
        }
      } catch (err) {
        console.error("Failed to parse alert:", err);
      }
    };

    return () => ws.close();
  }, [url, maxAlerts]);

  return { alerts, isConnected };
}
