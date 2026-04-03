// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL TYPE DEFINITIONS
// Financial Fraud Intelligence Platform
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Transaction object from data source
 */
export interface Transaction {
  txn_id: string;
  timestamp: string;
  amount: number;
  currency: string;
  merchant: string;
  user_id: string;
  location: string;
  device_id: string;
}

/**
 * ML Prediction result
 */
export interface Prediction {
  txn_id: string;
  is_fraud: boolean;
  risk_score: number;
  fraud_type: FraudType;
  action_taken: ActionType;
  shap_values: Record<string, number>;
  processing_time_ms: number;
}

/**
 * Combined transaction with prediction
 */
export interface TransactionWithPrediction extends Transaction {
  prediction?: Prediction;
}

/**
 * Fraud type classification
 */
export type FraudType =
  | "ACCOUNT_TAKEOVER"
  | "CARD_TESTING"
  | "FRAUD_RING"
  | "SYNTHETIC_IDENTITY"
  | "MONEY_MULE"
  | "LEGITIMATE";

/**
 * Action decision types
 */
export type ActionType = "ALLOW" | "BLOCK" | "MFA" | "REVIEW";

/**
 * Risk level classification
 */
export type RiskLevel = "safe" | "warning" | "critical";

/**
 * Alert object for fraud queue
 */
export interface FraudAlert {
  id: string;
  txn_id: string;
  timestamp: string;
  risk_score: number;
  fraud_type: FraudType;
  user_id: string;
  amount: number;
  currency: string;
  status: "pending" | "investigating" | "resolved" | "dismissed";
}

/**
 * Dashboard stats overview
 */
export interface DashboardStats {
  total_transactions: number;
  total_fraud_detected: number;
  avg_latency_ms: number;
  detection_rate: number;
  false_positive_rate: number;
  blocked_amount: number;
}

/**
 * SHAP value entry for explainability
 */
export interface ShapValue {
  feature: string;
  value: number;
  impact: "positive" | "negative";
}

/**
 * Investigation report from Mistral
 */
export interface InvestigationReport {
  txn_id: string;
  summary: string;
  evidence: string[];
  recommendations: string[];
  similar_cases: string[];
  confidence: number;
  generated_at: string;
}

/**
 * Graph node for Cytoscape visualization
 */
export interface GraphNode {
  id: string;
  type: "user" | "device" | "ip" | "card" | "merchant";
  label: string;
  risk_score?: number;
  is_fraud?: boolean;
}

/**
 * Graph edge for Cytoscape visualization
 */
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: "transaction" | "shared_device" | "shared_ip" | "transfer";
  weight?: number;
}

/**
 * Graph data structure
 */
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Attack scenario types for simulator
 */
export type AttackScenario =
  | "normal"
  | "account_takeover"
  | "card_testing"
  | "fraud_ring"
  | "synthetic_identity";

/**
 * Simulator control state
 */
export interface SimulatorState {
  isRunning: boolean;
  scenario: AttackScenario;
  transactionsPerSecond: number;
  attackIntensity: "low" | "medium" | "high";
}

/**
 * WebSocket message types
 */
export type WebSocketMessageType =
  | "transaction"
  | "alert"
  | "stats_update"
  | "system_status";

/**
 * WebSocket message structure
 */
export interface WebSocketMessage<T = unknown> {
  type: WebSocketMessageType;
  payload: T;
  timestamp: string;
}

/**
 * API response wrapper
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

/**
 * Metric card data
 */
export interface MetricData {
  label: string;
  value: number | string;
  unit?: string;
  change?: number;
  changeType?: "increase" | "decrease";
  icon?: string;
}
