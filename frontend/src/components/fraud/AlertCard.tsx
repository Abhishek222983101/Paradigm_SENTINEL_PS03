// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL ALERT CARD COMPONENT
// Fraud Alert Notification - Refined Design
// ═══════════════════════════════════════════════════════════════════════════

"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  ShieldAlert,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  User,
  DollarSign,
  Fingerprint,
  ChevronRight,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { FraudAlert } from "@/types";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface AlertCardProps {
  alert: FraudAlert;
  isNew?: boolean;
  onInvestigate?: (alert: FraudAlert) => void;
  onDismiss?: (alert: FraudAlert) => void;
  onResolve?: (alert: FraudAlert) => void;
  compact?: boolean;
  className?: string;
}

interface AlertQueueProps {
  alerts: FraudAlert[];
  maxDisplay?: number;
  onAlertClick?: (alert: FraudAlert) => void;
  className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

const fraudTypeLabels: Record<string, { label: string; icon: string }> = {
  ACCOUNT_TAKEOVER: { label: "Account Takeover", icon: "🔓" },
  CARD_TESTING: { label: "Card Testing", icon: "💳" },
  FRAUD_RING: { label: "Fraud Ring", icon: "🔗" },
  SYNTHETIC_IDENTITY: { label: "Synthetic ID", icon: "🎭" },
  MONEY_MULE: { label: "Money Mule", icon: "💰" },
  LEGITIMATE: { label: "Legitimate", icon: "✓" },
};

function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
  }).format(amount);
}

function formatTimeAgo(timestamp: string, now: Date): string {
  const then = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

// ═══════════════════════════════════════════════════════════════════════════
// ALERT CARD COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function AlertCard({
  alert,
  isNew = false,
  onInvestigate,
  onDismiss,
  onResolve,
  compact = false,
  className,
}: AlertCardProps) {
  const [isPulsing, setIsPulsing] = useState(isNew);
  const [currentTime, setCurrentTime] = useState<Date | null>(null);

  useEffect(() => {
    // Set time only on client to avoid hydration mismatch
    setCurrentTime(new Date());
    const interval = setInterval(() => setCurrentTime(new Date()), 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isNew) {
      const timer = setTimeout(() => setIsPulsing(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isNew]);

  const fraudInfo = fraudTypeLabels[alert.fraud_type] || fraudTypeLabels.LEGITIMATE;
  const isCritical = alert.risk_score >= 85;

  if (compact) {
    return (
      <motion.div
        initial={isNew ? { opacity: 0, x: -20, scale: 0.95 } : false}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 20, scale: 0.95 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className={cn(
          "relative p-3 cursor-pointer transition-all duration-200",
          "border-l-[3px] bg-[var(--bg-surface)] hover:bg-[var(--bg-overlay)]",
          "border-b border-[var(--border-subtle)]",
          isCritical ? "border-l-[var(--accent-danger)]" : "border-l-[var(--accent-warning)]",
          isPulsing && "ring-1 ring-[var(--accent-danger)]/30",
          className
        )}
      >
        <div className="flex items-center gap-3">
          <ShieldAlert
            className={cn(
              "w-5 h-5 flex-shrink-0",
              isCritical ? "text-[var(--accent-danger)]" : "text-[var(--accent-warning)]"
            )}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-[var(--accent-primary)] truncate">
                {alert.txn_id.slice(0, 16)}
              </span>
              <span
                className={cn(
                  "text-xs font-semibold px-1.5 py-0.5 rounded",
                  isCritical
                    ? "bg-[var(--accent-danger-glow)] text-[var(--accent-danger)]"
                    : "bg-[var(--accent-warning-glow)] text-[var(--accent-warning)]"
                )}
              >
                {alert.risk_score.toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-muted)]">
              <span>{fraudInfo.icon} {fraudInfo.label}</span>
              <span className="text-[var(--text-dim)]">•</span>
              <span>{formatCurrency(alert.amount, alert.currency)}</span>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[var(--text-dim)] flex-shrink-0" />
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={isNew ? { opacity: 0, y: -20, scale: 0.95 } : false}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={cn(
        "relative card overflow-hidden",
        isCritical && "border-[var(--accent-danger)]/50",
        isPulsing && "ring-2 ring-[var(--accent-danger)]/30",
        className
      )}
    >
      {/* Critical Alert Header */}
      {isCritical && (
        <div className="bg-[var(--accent-danger-glow)] px-4 py-2 border-b border-[var(--accent-danger)]/30 flex items-center gap-2 -mx-5 -mt-5 mb-4">
          <Zap className="w-4 h-4 text-[var(--accent-danger)]" />
          <span className="text-xs font-mono text-[var(--accent-danger)] uppercase tracking-wider font-semibold">
            Critical Alert - Immediate Action Required
          </span>
        </div>
      )}

      {/* Header Row */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "p-2 rounded-lg",
              isCritical
                ? "bg-[var(--accent-danger-glow)]"
                : "bg-[var(--accent-warning-glow)]"
            )}
          >
            <ShieldAlert
              className={cn(
                "w-6 h-6",
                isCritical ? "text-[var(--accent-danger)]" : "text-[var(--accent-warning)]"
              )}
            />
          </div>
          <div>
            <div className="font-mono text-sm text-[var(--accent-primary)]">
              {alert.id}
            </div>
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] mt-0.5">
              <Clock className="w-3 h-3" />
              {currentTime ? formatTimeAgo(alert.timestamp, currentTime) : "--"}
              <span className="text-[var(--text-dim)]">|</span>
              <span className="text-[var(--text-primary)] font-medium">
                {fraudInfo.icon} {fraudInfo.label}
              </span>
            </div>
          </div>
        </div>

        {/* Risk Score Badge */}
        <div
          className={cn(
            "text-center px-4 py-2 rounded-lg font-mono font-bold",
            isCritical
              ? "bg-[var(--accent-danger-glow)] text-[var(--accent-danger)] border border-[var(--accent-danger)]/30"
              : "bg-[var(--accent-warning-glow)] text-[var(--accent-warning)] border border-[var(--accent-warning)]/30"
          )}
        >
          <div className="text-2xl">{alert.risk_score.toFixed(0)}</div>
          <div className="text-[10px] opacity-70 uppercase">Risk</div>
        </div>
      </div>

      {/* Transaction Details */}
      <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-[var(--text-dim)]" />
          <div>
            <div className="data-label">Amount</div>
            <div className="font-mono font-semibold text-[var(--text-primary)]">
              {formatCurrency(alert.amount, alert.currency)}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-[var(--text-dim)]" />
          <div>
            <div className="data-label">User</div>
            <div className="font-mono text-[var(--text-primary)]">{alert.user_id}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Fingerprint className="w-4 h-4 text-[var(--text-dim)]" />
          <div>
            <div className="data-label">Transaction</div>
            <div className="font-mono text-[var(--text-primary)] truncate">
              {alert.txn_id.slice(0, 12)}
            </div>
          </div>
        </div>
      </div>

      {/* Status Badge */}
      <div className="flex items-center gap-2 mb-4">
        <span className="data-label">Status:</span>
        <span
          className={cn(
            "px-2 py-0.5 rounded-full text-xs font-mono uppercase",
            {
              pending: "bg-[var(--accent-warning-glow)] text-[var(--accent-warning)]",
              investigating: "bg-[var(--accent-primary-glow)] text-[var(--accent-primary)]",
              resolved: "bg-[var(--accent-success-glow)] text-[var(--accent-success)]",
              dismissed: "bg-[var(--bg-muted)] text-[var(--text-muted)]",
            }[alert.status]
          )}
        >
          {alert.status}
        </span>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => onInvestigate?.(alert)}
          className="btn btn-primary flex-1"
        >
          <Eye className="w-4 h-4" />
          Investigate
        </button>
        <button
          onClick={() => onResolve?.(alert)}
          className="btn btn-success"
        >
          <CheckCircle className="w-4 h-4" />
        </button>
        <button
          onClick={() => onDismiss?.(alert)}
          className="btn btn-ghost"
        >
          <XCircle className="w-4 h-4" />
        </button>
      </div>

      {/* Pulsing border effect for new alerts */}
      {isPulsing && (
        <motion.div
          className="absolute inset-0 border-2 border-[var(--accent-danger)] rounded-[var(--radius-lg)] pointer-events-none"
          initial={{ opacity: 1 }}
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// ALERT QUEUE COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function AlertQueue({
  alerts,
  maxDisplay = 10,
  onAlertClick,
  className,
}: AlertQueueProps) {
  const displayedAlerts = alerts.slice(0, maxDisplay);
  const pendingCount = alerts.filter((a) => a.status === "pending").length;
  const criticalCount = alerts.filter((a) => a.risk_score >= 85).length;

  return (
    <div className={cn("flex flex-col h-full panel p-0 overflow-hidden", className)}>
      {/* Header */}
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-[var(--accent-danger)]" />
          <span className="panel-title text-[var(--accent-danger)]">
            Fraud Alerts
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-[var(--accent-warning)]">{pendingCount} pending</span>
          {criticalCount > 0 && (
            <motion.span 
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="text-[var(--accent-danger)]"
            >
              {criticalCount} critical
            </motion.span>
          )}
        </div>
      </div>

      {/* Alert List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {displayedAlerts.length > 0 ? (
            displayedAlerts.map((alert, idx) => (
              <AlertCard
                key={`${alert.id}-${idx}`}
                alert={alert}
                isNew={idx === 0}
                compact
                onInvestigate={() => onAlertClick?.(alert)}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12 text-[var(--text-muted)]"
            >
              <ShieldAlert className="w-10 h-10 mb-3 opacity-30" />
              <div className="font-mono text-sm uppercase tracking-wider">
                No Active Alerts
              </div>
              <div className="text-xs mt-1 opacity-50">
                System monitoring active
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      {alerts.length > maxDisplay && (
        <div className="px-4 py-2 bg-[var(--bg-elevated)] border-t border-[var(--border-default)]">
          <button className="w-full text-center text-xs font-mono text-[var(--accent-primary)] hover:text-[var(--accent-primary-dim)] transition-colors">
            View all {alerts.length} alerts →
          </button>
        </div>
      )}
    </div>
  );
}

export default AlertCard;
