// ============================================================================
// SENTINEL DASHBOARD - Command Center
// Real-Time Fraud Monitoring with refined, readable design
// ============================================================================

"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  Shield,
  ShieldAlert,
  Zap,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Server,
  Wifi,
  WifiOff,
  RefreshCw,
  Pause,
  Play,
  X,
  ChevronRight,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTransactionStream } from "@/hooks";
import { TransactionFeed, AlertQueue, RiskGauge } from "@/components/fraud";
import { FloatingHeader } from "@/components/layout";
import type { TransactionWithPrediction } from "@/types";

// ============================================================================
// STAT CARD COMPONENT
// ============================================================================

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  change?: number;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

function StatCard({ label, value, icon, change, variant = "default" }: StatCardProps) {
  const variantStyles = {
    default: "",
    success: "border-l-[3px] border-l-[#34d399]",
    warning: "border-l-[3px] border-l-[#fbbf24]",
    danger: "border-l-[3px] border-l-[#f87171]",
    info: "border-l-[3px] border-l-[#38bdf8]",
  };

  const iconColors = {
    default: "text-[#64748b]",
    success: "text-[#34d399]",
    warning: "text-[#fbbf24]",
    danger: "text-[#f87171]",
    info: "text-[#38bdf8]",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[10px] p-4",
        "hover:border-[rgba(148,163,184,0.15)] hover:bg-[#1a222d] transition-all duration-200",
        variantStyles[variant]
      )}
    >
      <div className="flex items-start justify-between mb-3">
        <div className={cn("p-2 rounded-lg bg-[#0f1419]", iconColors[variant])}>
          {icon}
        </div>
        {change !== undefined && change !== 0 && (
          <div
            className={cn(
              "flex items-center gap-1 text-[11px] font-mono font-medium",
              change > 0 ? "text-[#f87171]" : "text-[#34d399]"
            )}
          >
            {change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {Math.abs(change).toFixed(1)}%
          </div>
        )}
      </div>
      
      <div className="font-mono text-[10px] uppercase tracking-[0.08em] text-[#64748b] mb-1">
        {label}
      </div>
      <div className="font-mono text-xl font-semibold text-[#f0f4f8] tracking-tight">
        {value}
      </div>
    </motion.div>
  );
}

// ============================================================================
// CONNECTION STATUS
// ============================================================================

function ConnectionStatus({
  isConnected,
  isReconnecting,
  attackActive,
}: {
  isConnected: boolean;
  isReconnecting: boolean;
  attackActive: string | null;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-mono font-medium uppercase tracking-wider",
          isConnected
            ? "bg-[rgba(52,211,153,0.12)] text-[#34d399] border border-[rgba(52,211,153,0.25)]"
            : isReconnecting
            ? "bg-[rgba(251,191,36,0.12)] text-[#fbbf24] border border-[rgba(251,191,36,0.25)]"
            : "bg-[rgba(248,113,113,0.12)] text-[#f87171] border border-[rgba(248,113,113,0.25)]"
        )}
      >
        {isConnected ? (
          <>
            <span className="w-1.5 h-1.5 rounded-full bg-[#34d399] animate-pulse" />
            <span>Live</span>
          </>
        ) : isReconnecting ? (
          <>
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>Reconnecting</span>
          </>
        ) : (
          <>
            <WifiOff className="w-3 h-3" />
            <span>Offline</span>
          </>
        )}
      </div>

      <AnimatePresence>
        {attackActive && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, x: -8 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95, x: -8 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[rgba(248,113,113,0.12)] border border-[rgba(248,113,113,0.25)]"
          >
            <AlertTriangle className="w-3 h-3 text-[#f87171]" />
            <span className="text-[11px] font-mono font-medium text-[#f87171] uppercase tracking-wider">
              Attack: {attackActive.replace("_", " ")}
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#f87171] animate-pulse" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// MAIN DASHBOARD
// ============================================================================

export default function DashboardPage() {
  const [selectedTransaction, setSelectedTransaction] = useState<TransactionWithPrediction | null>(null);
  const [currentTime, setCurrentTime] = useState<string>("--:--:--");

  const {
    transactions,
    alerts,
    isConnected,
    isReconnecting,
    attackActive,
    connect,
    disconnect,
    clearTransactions,
    requestStats,
  } = useTransactionStream({
    maxTransactions: 100,
    autoReconnect: true,
  });

  const isConnectedRef = useRef(isConnected);
  isConnectedRef.current = isConnected;

  // Update time only on client to avoid hydration mismatch
  useEffect(() => {
    setCurrentTime(new Date().toLocaleTimeString());
    const interval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (isConnectedRef.current) requestStats();
    }, 5000);
    return () => clearInterval(interval);
  }, [requestStats]);

  const liveStats = {
    totalTransactions: transactions.length,
    fraudCount: transactions.filter((t) => t.prediction?.is_fraud).length,
    blockedCount: transactions.filter((t) => t.prediction?.action_taken === "BLOCK").length,
    avgLatency: transactions.length > 0
      ? (transactions.reduce((acc, t) => acc + (t.prediction?.processing_time_ms ?? 0), 0) / transactions.length).toFixed(1)
      : "0",
    blockedAmount: transactions
      .filter((t) => t.prediction?.action_taken === "BLOCK")
      .reduce((acc, t) => acc + t.amount, 0),
    criticalAlerts: alerts.filter((a) => a.risk_score >= 85).length,
  };

  const avgRiskScore = transactions.length > 0
    ? Math.round(transactions.reduce((acc, t) => acc + (t.prediction?.risk_score ?? 0), 0) / transactions.length)
    : 0;

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      <FloatingHeader />

      <main className="pt-20 px-6 pb-8">
        <div className="max-w-[1800px] mx-auto">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-semibold text-[#f0f4f8] tracking-tight mb-1" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Command Center
              </h1>
              <p className="text-[13px] text-[#64748b]">
                Real-time fraud detection and transaction monitoring
              </p>
            </div>
            <ConnectionStatus
              isConnected={isConnected}
              isReconnecting={isReconnecting}
              attackActive={attackActive}
            />
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <StatCard
              label="Transactions"
              value={liveStats.totalTransactions.toLocaleString()}
              icon={<Activity className="w-4 h-4" />}
              variant="info"
            />
            <StatCard
              label="Fraud Detected"
              value={liveStats.fraudCount}
              icon={<ShieldAlert className="w-4 h-4" />}
              variant={liveStats.fraudCount > 0 ? "danger" : "success"}
              change={liveStats.fraudCount > 0 ? 12.5 : 0}
            />
            <StatCard
              label="Blocked"
              value={liveStats.blockedCount}
              icon={<Shield className="w-4 h-4" />}
              variant="warning"
            />
            <StatCard
              label="Avg Latency"
              value={`${liveStats.avgLatency}ms`}
              icon={<Zap className="w-4 h-4" />}
              variant="success"
            />
            <StatCard
              label="Blocked Amount"
              value={`$${liveStats.blockedAmount.toLocaleString()}`}
              icon={<DollarSign className="w-4 h-4" />}
              variant="danger"
            />
            <StatCard
              label="Critical Alerts"
              value={liveStats.criticalAlerts}
              icon={<AlertTriangle className="w-4 h-4" />}
              variant={liveStats.criticalAlerts > 0 ? "danger" : "default"}
            />
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6" style={{ minHeight: 'calc(100vh - 340px)' }}>
            {/* Transaction Feed Panel */}
            <div className="lg:col-span-8 bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[14px] overflow-hidden flex flex-col">
              <div className="flex items-center justify-between px-4 py-3 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#34d399] animate-pulse" />
                  <span className="text-[13px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    Live Transaction Feed
                  </span>
                </div>
                <span className="text-[11px] font-mono text-[#64748b]">
                  {transactions.length} in buffer
                </span>
              </div>
              <TransactionFeed
                transactions={transactions}
                maxDisplay={50}
                onTransactionClick={setSelectedTransaction}
                className="flex-1"
              />
            </div>

            {/* Right Sidebar */}
            <div className="lg:col-span-4 flex flex-col gap-6">
              {/* Risk Gauge */}
              <div className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[14px] p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Activity className="w-4 h-4 text-[#38bdf8]" />
                  <span className="text-[13px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    System Risk Level
                  </span>
                </div>
                <RiskGauge
                  value={avgRiskScore}
                  size="lg"
                  label="Average Risk Score"
                  className="mx-auto"
                />
              </div>

              {/* Alert Queue */}
              <div className="flex-1 bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[14px] overflow-hidden flex flex-col min-h-[300px]">
                <div className="flex items-center justify-between px-4 py-3 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[#f87171]" />
                    <span className="text-[13px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      Fraud Alerts
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-[#f87171]">
                    {alerts.length} pending
                  </span>
                </div>
                <AlertQueue
                  alerts={alerts}
                  maxDisplay={10}
                  onAlertClick={(alert) => {
                    const txn = transactions.find((t) => t.txn_id === alert.txn_id);
                    if (txn) setSelectedTransaction(txn);
                  }}
                />
              </div>
            </div>
          </div>

          {/* Footer Controls */}
          <div className="mt-6 flex items-center justify-between px-5 py-3.5 bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[10px]">
            <div className="flex items-center gap-3">
              <button
                onClick={() => (isConnected ? disconnect() : connect())}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-md text-[12px] font-medium transition-all",
                  isConnected
                    ? "bg-transparent border border-[rgba(248,113,113,0.3)] text-[#f87171] hover:bg-[rgba(248,113,113,0.08)]"
                    : "bg-transparent border border-[rgba(52,211,153,0.3)] text-[#34d399] hover:bg-[rgba(52,211,153,0.08)]"
                )}
              >
                {isConnected ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                {isConnected ? "Disconnect" : "Connect"}
              </button>

              <button
                onClick={clearTransactions}
                className="flex items-center gap-2 px-4 py-2 rounded-md border border-[rgba(148,163,184,0.12)] text-[12px] font-medium text-[#94a3b8] hover:bg-[#1a222d] hover:text-[#f0f4f8] transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Clear Buffer
              </button>
            </div>

            <div className="flex items-center gap-6 text-[11px] font-mono text-[#64748b]">
              <div className="flex items-center gap-2">
                <Server className="w-3.5 h-3.5" />
                Backend: {isConnected ? <span className="text-[#34d399]">Connected</span> : <span className="text-[#f87171]">Offline</span>}
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-3.5 h-3.5" />
                {currentTime}
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-3.5 h-3.5" />
                Buffer: {transactions.length}/100
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Transaction Detail Modal */}
      <AnimatePresence>
        {selectedTransaction && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-[#0a0e14]/90 backdrop-blur-sm flex items-center justify-center p-6"
            onClick={() => setSelectedTransaction(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="bg-[#151b23] border border-[rgba(148,163,184,0.12)] rounded-[16px] p-6 max-w-lg w-full shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-5">
                <div>
                  <h2 className="text-lg font-semibold text-[#f0f4f8] mb-1" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    Transaction Details
                  </h2>
                  <p className="text-[12px] font-mono text-[#64748b]">
                    {selectedTransaction.txn_id}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedTransaction(null)}
                  className="p-1.5 rounded-md hover:bg-[#1a222d] text-[#64748b] hover:text-[#f0f4f8] transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-5">
                {[
                  { label: "Amount", value: `$${selectedTransaction.amount.toLocaleString()}` },
                  { label: "Merchant", value: selectedTransaction.merchant },
                  { label: "Location", value: selectedTransaction.location },
                  { 
                    label: "Risk Score", 
                    value: `${selectedTransaction.prediction?.risk_score?.toFixed(0) ?? 0}%`,
                    color: (selectedTransaction.prediction?.risk_score ?? 0) >= 70 ? "#f87171" : (selectedTransaction.prediction?.risk_score ?? 0) >= 40 ? "#fbbf24" : "#34d399"
                  },
                  { 
                    label: "Fraud Type", 
                    value: selectedTransaction.prediction?.fraud_type?.replace("_", " ") || "N/A",
                    color: "#fbbf24"
                  },
                  { 
                    label: "Action", 
                    value: selectedTransaction.prediction?.action_taken || "N/A",
                    color: selectedTransaction.prediction?.action_taken === "BLOCK" ? "#f87171" : selectedTransaction.prediction?.action_taken === "MFA" ? "#fbbf24" : "#34d399"
                  },
                ].map((item) => (
                  <div key={item.label} className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">{item.label}</div>
                    <div className="text-[14px] font-medium" style={{ color: item.color || "#f0f4f8" }}>{item.value}</div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => window.location.href = `/investigation/${selectedTransaction.txn_id}`}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] text-[#38bdf8] text-[13px] font-medium hover:bg-[rgba(56,189,248,0.15)] transition-all"
                >
                  Investigate
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setSelectedTransaction(null)}
                  className="px-5 py-2.5 rounded-lg border border-[rgba(148,163,184,0.12)] text-[#94a3b8] text-[13px] font-medium hover:bg-[#1a222d] hover:text-[#f0f4f8] transition-all"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
