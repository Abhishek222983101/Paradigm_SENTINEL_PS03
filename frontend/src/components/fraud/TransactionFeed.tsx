// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL TRANSACTION FEED COMPONENT
// Real-Time Transaction Stream - Refined Design
// ═══════════════════════════════════════════════════════════════════════════

"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Clock,
  MapPin,
  Smartphone,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { TransactionWithPrediction, RiskLevel } from "@/types";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface TransactionFeedProps {
  transactions: TransactionWithPrediction[];
  maxDisplay?: number;
  expandable?: boolean;
  onTransactionClick?: (txn: TransactionWithPrediction) => void;
  className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function getRiskLevel(score: number): RiskLevel {
  if (score >= 70) return "critical";
  if (score >= 40) return "warning";
  return "safe";
}

function formatAmount(amount: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

// ═══════════════════════════════════════════════════════════════════════════
// TRANSACTION ROW COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface TransactionRowProps {
  transaction: TransactionWithPrediction;
  isNew?: boolean;
  onClick?: () => void;
}

function TransactionRow({ transaction, isNew, onClick }: TransactionRowProps) {
  const riskScore = transaction.prediction?.risk_score ?? 0;
  const riskLevel = getRiskLevel(riskScore);
  const isFraud = transaction.prediction?.is_fraud ?? false;
  const action = transaction.prediction?.action_taken ?? "ALLOW";

  const riskStyles = {
    safe: {
      border: "border-l-[var(--accent-success)]",
      hover: "hover:bg-[var(--accent-success-glow)]",
      badge: "bg-[var(--accent-success-glow)] text-[var(--accent-success)] border-[var(--accent-success)]/30",
    },
    warning: {
      border: "border-l-[var(--accent-warning)]",
      hover: "hover:bg-[var(--accent-warning-glow)]",
      badge: "bg-[var(--accent-warning-glow)] text-[var(--accent-warning)] border-[var(--accent-warning)]/30",
    },
    critical: {
      border: "border-l-[var(--accent-danger)]",
      hover: "hover:bg-[var(--accent-danger-glow)]",
      badge: "bg-[var(--accent-danger-glow)] text-[var(--accent-danger)] border-[var(--accent-danger)]/30",
    },
  };

  const actionStyles: Record<string, string> = {
    ALLOW: "bg-[var(--accent-success-glow)] text-[var(--accent-success)]",
    BLOCK: "bg-[var(--accent-danger-glow)] text-[var(--accent-danger)]",
    MFA: "bg-[var(--accent-warning-glow)] text-[var(--accent-warning)]",
    REVIEW: "bg-[var(--accent-primary-glow)] text-[var(--accent-primary)]",
  };

  const style = riskStyles[riskLevel];

  return (
    <motion.div
      initial={isNew ? { opacity: 0, x: -20, backgroundColor: "rgba(56, 189, 248, 0.1)" } : false}
      animate={{ opacity: 1, x: 0, backgroundColor: "transparent" }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      onClick={onClick}
      className={cn(
        "data-row cursor-pointer",
        style.border,
        style.hover,
        "border-l-[3px]",
        isNew && "ring-1 ring-[var(--accent-primary)]/20"
      )}
    >
      {/* Scanline effect for new transactions */}
      {isNew && (
        <motion.div
          initial={{ top: 0 }}
          animate={{ top: "100%" }}
          transition={{ duration: 0.5, ease: "linear" }}
          className="absolute left-0 right-0 h-px bg-[var(--accent-primary)]/50"
        />
      )}

      <div className="flex items-center gap-4 w-full">
        {/* Status Icon */}
        <div className="flex-shrink-0">
          {riskLevel === "critical" ? (
            <ShieldAlert className="w-5 h-5 text-[var(--accent-danger)]" />
          ) : riskLevel === "warning" ? (
            <Shield className="w-5 h-5 text-[var(--accent-warning)]" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-[var(--accent-success)]" />
          )}
        </div>

        {/* Transaction ID & Time */}
        <div className="flex-shrink-0 w-48">
          <div className="text-[var(--accent-primary)] font-mono font-medium text-xs tracking-wide">
            {transaction.txn_id.slice(0, 20)}
          </div>
          <div className="flex items-center gap-1 text-[var(--text-muted)] text-xs mt-0.5">
            <Clock className="w-3 h-3" />
            {formatTime(transaction.timestamp)}
          </div>
        </div>

        {/* Amount */}
        <div className="flex-shrink-0 w-28 text-right">
          <span
            className={cn(
              "font-mono font-semibold",
              isFraud ? "text-[var(--accent-danger)]" : "text-[var(--text-primary)]"
            )}
          >
            {formatAmount(transaction.amount, transaction.currency)}
          </span>
        </div>

        {/* Merchant */}
        <div className="flex-1 min-w-0">
          <div className="text-[var(--text-primary)] truncate text-sm">
            {truncate(transaction.merchant, 20)}
          </div>
          <div className="flex items-center gap-1 text-[var(--text-muted)] text-xs mt-0.5">
            <MapPin className="w-3 h-3" />
            {truncate(transaction.location, 15)}
          </div>
        </div>

        {/* User ID */}
        <div className="flex-shrink-0 w-24">
          <div className="text-[var(--text-muted)] text-xs font-mono">{transaction.user_id}</div>
          <div className="flex items-center gap-1 text-[var(--text-dim)] text-xs mt-0.5">
            <Smartphone className="w-3 h-3" />
            {transaction.device_id.split("-").slice(0, 2).join("-")}
          </div>
        </div>

        {/* Risk Score Badge */}
        <div
          className={cn(
            "flex-shrink-0 w-16 text-center py-1 px-2 rounded-md border font-mono font-semibold text-xs",
            style.badge
          )}
        >
          {riskScore.toFixed(0)}%
        </div>

        {/* Action Badge */}
        <div
          className={cn(
            "flex-shrink-0 w-16 text-center py-1 px-2 rounded-md font-mono font-medium text-xs uppercase",
            actionStyles[action] || actionStyles.ALLOW
          )}
        >
          {action}
        </div>

        {/* Processing Time */}
        <div className="flex-shrink-0 w-14 text-right text-[var(--text-muted)] text-xs font-mono">
          {transaction.prediction?.processing_time_ms?.toFixed(0) ?? "--"}ms
        </div>

        {/* Expand Arrow */}
        <ChevronRight className="w-4 h-4 text-[var(--text-dim)] flex-shrink-0" />
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function TransactionFeed({
  transactions,
  maxDisplay = 20,
  expandable = true,
  onTransactionClick,
  className,
}: TransactionFeedProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const prevLatestIdRef = useRef<string | null>(null);
  const [newTxnId, setNewTxnId] = useState<string | null>(null);

  // Track new transactions for animation - only track the latest one
  useEffect(() => {
    if (transactions.length > 0) {
      const latestId = transactions[0].txn_id;
      // Only trigger if this is actually a new transaction
      if (latestId !== prevLatestIdRef.current) {
        prevLatestIdRef.current = latestId;
        setNewTxnId(latestId);
        const timer = setTimeout(() => {
          setNewTxnId(null);
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [transactions.length]);

  const displayedTransactions = transactions.slice(0, maxDisplay);

  return (
    <div className={cn("flex flex-col panel p-0 overflow-hidden", className)}>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <span className="status-dot live" />
          <span className="panel-title">
            Live Transaction Feed
          </span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-mono">
          {transactions.length} TXN in buffer
        </div>
      </div>

      {/* Column Headers */}
      <div className="table-header gap-4">
        <div className="w-5" />
        <div className="w-48">TXN ID / Time</div>
        <div className="w-28 text-right">Amount</div>
        <div className="flex-1">Merchant / Location</div>
        <div className="w-24">User / Device</div>
        <div className="w-16 text-center">Risk</div>
        <div className="w-16 text-center">Action</div>
        <div className="w-14 text-right">Latency</div>
        <div className="w-4" />
      </div>

      {/* Transaction List */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto"
      >
        <AnimatePresence mode="popLayout">
          {displayedTransactions.length > 0 ? (
            displayedTransactions.map((txn, idx) => (
              <TransactionRow
                key={`${txn.txn_id}-${idx}`}
                transaction={txn}
                isNew={txn.txn_id === newTxnId}
                onClick={() => onTransactionClick?.(txn)}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12 text-[var(--text-muted)]"
            >
              <Shield className="w-12 h-12 mb-4 opacity-30" />
              <div className="font-mono text-sm uppercase tracking-wider">
                Awaiting transactions...
              </div>
              <div className="text-xs mt-2 opacity-50">
                Connect to WebSocket to begin streaming
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-elevated)] border-t border-[var(--border-default)] text-xs font-mono">
        <div className="flex items-center gap-4">
          <span className="text-[var(--accent-success)] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-success)]" />
            Safe: {transactions.filter((t) => getRiskLevel(t.prediction?.risk_score ?? 0) === "safe").length}
          </span>
          <span className="text-[var(--accent-warning)] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-warning)]" />
            Warn: {transactions.filter((t) => getRiskLevel(t.prediction?.risk_score ?? 0) === "warning").length}
          </span>
          <span className="text-[var(--accent-danger)] flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-danger)]" />
            Crit: {transactions.filter((t) => getRiskLevel(t.prediction?.risk_score ?? 0) === "critical").length}
          </span>
        </div>
        <div className="text-[var(--text-muted)]">
          Buffer: {maxDisplay - displayedTransactions.length} slots remaining
        </div>
      </div>
    </div>
  );
}

export default TransactionFeed;
