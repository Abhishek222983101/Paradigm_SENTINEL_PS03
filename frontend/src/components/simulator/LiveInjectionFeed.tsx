// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL LIVE INJECTION FEED
// Real-time visualization of injected attack transactions - Refined Design
// ═══════════════════════════════════════════════════════════════════════════

"use client";

import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { TransactionWithPrediction, AttackScenario } from "@/types";
import {
  AlertTriangle,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Zap,
  Clock,
  ChevronRight,
  Terminal,
} from "lucide-react";

// ═══════════════════════════════════════════════════════════════════════════
// INJECTED TRANSACTION ROW
// ═══════════════════════════════════════════════════════════════════════════

interface InjectedTransactionRowProps {
  transaction: TransactionWithPrediction;
  index: number;
  onInspect?: (txn: TransactionWithPrediction) => void;
}

function InjectedTransactionRow({
  transaction,
  index,
  onInspect,
}: InjectedTransactionRowProps) {
  const prediction = transaction.prediction;
  const riskScore = prediction?.risk_score ?? 0;
  const isFraud = prediction?.is_fraud ?? false;
  const action = prediction?.action_taken ?? "ALLOW";

  const getRiskStyles = () => {
    if (riskScore >= 80) return { color: "var(--accent-danger)", bg: "var(--accent-danger-glow)" };
    if (riskScore >= 50) return { color: "var(--accent-warning)", bg: "var(--accent-warning-glow)" };
    return { color: "var(--accent-success)", bg: "var(--accent-success-glow)" };
  };

  const riskStyles = getRiskStyles();

  const getActionIcon = () => {
    switch (action) {
      case "BLOCK":
        return <ShieldAlert className="w-4 h-4 text-[var(--accent-danger)]" />;
      case "MFA":
        return <Shield className="w-4 h-4 text-[var(--accent-warning)]" />;
      case "REVIEW":
        return <AlertTriangle className="w-4 h-4 text-[var(--accent-warning)]" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-[var(--accent-success)]" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, height: 0 }}
      animate={{ opacity: 1, x: 0, height: "auto" }}
      exit={{ opacity: 0, x: 20, height: 0 }}
      transition={{ duration: 0.15, delay: index * 0.02 }}
      className={cn(
        "group flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors",
        "border-l-3 bg-[var(--bg-elevated)]/50 hover:bg-[var(--bg-overlay)]",
        isFraud ? "border-l-[var(--accent-danger)]" : "border-l-transparent"
      )}
      style={{ borderLeftWidth: '3px' }}
      onClick={() => onInspect?.(transaction)}
    >
      {/* Timestamp */}
      <div className="w-20 text-[11px] font-mono text-[var(--text-muted)] flex-shrink-0">
        {new Date(transaction.timestamp).toLocaleTimeString()}
      </div>

      {/* Transaction ID */}
      <div className="w-24 text-xs font-mono text-[var(--accent-primary)] truncate flex-shrink-0">
        {transaction.txn_id.slice(0, 8)}...
      </div>

      {/* Amount */}
      <div className="w-24 text-sm font-mono font-medium text-[var(--text-primary)] flex-shrink-0">
        ${transaction.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
      </div>

      {/* Merchant */}
      <div className="flex-1 text-xs font-mono text-[var(--text-muted)] truncate">
        {transaction.merchant}
      </div>

      {/* Risk Score Bar */}
      <div className="w-32 flex items-center gap-2 flex-shrink-0">
        <div className="flex-1 h-1.5 bg-[var(--bg-muted)] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${riskScore}%` }}
            transition={{ duration: 0.3 }}
            className="h-full rounded-full"
            style={{ backgroundColor: riskStyles.color }}
          />
        </div>
        <span
          className="text-xs font-mono font-semibold w-8 text-right"
          style={{ color: riskStyles.color }}
        >
          {riskScore.toFixed(0)}
        </span>
      </div>

      {/* Fraud Type */}
      <div className="w-28 flex-shrink-0">
        {isFraud && (
          <span
            className="inline-block px-2 py-0.5 text-[9px] font-mono uppercase tracking-wider rounded"
            style={{ 
              backgroundColor: "var(--accent-danger-glow)", 
              color: "var(--accent-danger)",
              border: "1px solid rgba(248, 113, 113, 0.3)"
            }}
          >
            {prediction?.fraud_type?.replace("_", " ").slice(0, 12)}
          </span>
        )}
      </div>

      {/* Action */}
      <div className="w-8 flex-shrink-0 flex justify-center">
        {getActionIcon()}
      </div>

      {/* Inspect arrow */}
      <ChevronRight className="w-4 h-4 text-[var(--text-dim)] opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface LiveInjectionFeedProps {
  transactions: TransactionWithPrediction[];
  attackScenario: AttackScenario | null;
  isRunning: boolean;
  maxDisplay?: number;
  onInspect?: (txn: TransactionWithPrediction) => void;
  className?: string;
}

export function LiveInjectionFeed({
  transactions,
  attackScenario,
  isRunning,
  maxDisplay = 30,
  onInspect,
  className,
}: LiveInjectionFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);
  const displayTransactions = transactions.slice(0, maxDisplay);
  const [currentTime, setCurrentTime] = useState<string>("--:--:--");

  // Update time only on client to avoid hydration mismatch
  useEffect(() => {
    setCurrentTime(new Date().toLocaleTimeString());
    const interval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to top when new transactions arrive
  useEffect(() => {
    if (feedRef.current && transactions.length > 0) {
      feedRef.current.scrollTop = 0;
    }
  }, [transactions.length]);

  // Calculate live stats
  const stats = {
    total: transactions.length,
    fraudCount: transactions.filter((t) => t.prediction?.is_fraud).length,
    blockedCount: transactions.filter((t) => t.prediction?.action_taken === "BLOCK").length,
    avgRisk:
      transactions.length > 0
        ? transactions.reduce((acc, t) => acc + (t.prediction?.risk_score ?? 0), 0) /
          transactions.length
        : 0,
  };

  const getAvgRiskColor = () => {
    if (stats.avgRisk >= 60) return "var(--accent-danger)";
    if (stats.avgRisk >= 40) return "var(--accent-warning)";
    return "var(--accent-success)";
  };

  return (
    <div className={cn("flex flex-col h-full panel p-0 overflow-hidden", className)}>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "p-2 rounded-lg",
              isRunning
                ? "bg-[var(--accent-danger-glow)]"
                : "bg-[var(--accent-primary-glow)]"
            )}
          >
            <Terminal
              className={cn(
                "w-4 h-4",
                isRunning ? "text-[var(--accent-danger)]" : "text-[var(--accent-primary)]"
              )}
            />
          </div>
          <div>
            <h3 className="panel-title">
              Injection Feed
            </h3>
            {attackScenario && isRunning && (
              <p className="text-[10px] text-[var(--accent-danger)] font-mono uppercase">
                {attackScenario.replace("_", " ")} in progress
              </p>
            )}
          </div>
        </div>

        {/* Live indicator */}
        {isRunning && (
          <motion.div
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="status-badge bg-[var(--accent-danger-glow)] text-[var(--accent-danger)] border border-[var(--accent-danger)]/30"
          >
            <span className="status-dot bg-[var(--accent-danger)]" />
            Live
          </motion.div>
        )}
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-4 border-b border-[var(--border-default)] bg-[var(--bg-elevated)]">
        <div className="px-4 py-2.5 border-r border-[var(--border-subtle)]">
          <div className="data-label">Total</div>
          <div className="text-lg font-bold font-mono text-[var(--accent-primary)]">
            {stats.total}
          </div>
        </div>
        <div className="px-4 py-2.5 border-r border-[var(--border-subtle)]">
          <div className="data-label">Fraud</div>
          <div className="text-lg font-bold font-mono text-[var(--accent-danger)]">
            {stats.fraudCount}
          </div>
        </div>
        <div className="px-4 py-2.5 border-r border-[var(--border-subtle)]">
          <div className="data-label">Blocked</div>
          <div className="text-lg font-bold font-mono text-[var(--accent-warning)]">
            {stats.blockedCount}
          </div>
        </div>
        <div className="px-4 py-2.5">
          <div className="data-label">Avg Risk</div>
          <div
            className="text-lg font-bold font-mono"
            style={{ color: getAvgRiskColor() }}
          >
            {stats.avgRisk.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Column Headers */}
      <div className="table-header gap-3">
        <div className="w-20">Time</div>
        <div className="w-24">TXN ID</div>
        <div className="w-24">Amount</div>
        <div className="flex-1">Merchant</div>
        <div className="w-32">Risk Score</div>
        <div className="w-28">Type</div>
        <div className="w-8">Act</div>
        <div className="w-4"></div>
      </div>

      {/* Transaction Feed */}
      <div
        ref={feedRef}
        className="flex-1 overflow-y-auto overflow-x-hidden divide-y divide-[var(--border-subtle)]"
      >
        <AnimatePresence mode="popLayout">
          {displayTransactions.length > 0 ? (
            displayTransactions.map((txn, idx) => (
              <InjectedTransactionRow
                key={`${txn.txn_id}-${idx}`}
                transaction={txn}
                index={idx}
                onInspect={onInspect}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-full py-12 text-center"
            >
              <Activity className="w-12 h-12 text-[var(--text-dim)] mb-4" />
              <p className="text-sm text-[var(--text-muted)] font-mono">
                {isRunning
                  ? "Waiting for transactions..."
                  : "No transactions. Start an attack to see the feed."}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-elevated)] border-t border-[var(--border-default)] text-[10px] font-mono text-[var(--text-muted)]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <Clock className="w-3 h-3" />
            {currentTime}
          </span>
          <span className="flex items-center gap-1.5">
            <Zap className="w-3 h-3" />
            {transactions.length > 0
              ? `${transactions[0]?.prediction?.processing_time_ms?.toFixed(0) ?? 0}ms latency`
              : "-- ms latency"}
          </span>
        </div>
        <div>
          Showing {displayTransactions.length} of {transactions.length}
        </div>
      </div>
    </div>
  );
}

export default LiveInjectionFeed;
