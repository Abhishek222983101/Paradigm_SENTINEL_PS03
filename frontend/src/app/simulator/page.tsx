// ============================================================================
// SENTINEL SIMULATOR PAGE
// Attack Injection & Testing Lab - Refined Design
// ============================================================================

"use client";

import { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useTransactionStream } from "@/hooks";
import { FloatingHeader } from "@/components/layout";
import {
  AttackScenarioGrid,
  SimulatorControls,
  LiveInjectionFeed,
  type AttackIntensity,
} from "@/components/simulator";
import type { AttackScenario, TransactionWithPrediction } from "@/types";
import {
  Beaker,
  AlertTriangle,
  Activity,
  Shield,
  Wifi,
  WifiOff,
  RefreshCw,
  Target,
  BarChart3,
  Zap,
  Clock,
  ChevronRight,
  ExternalLink,
  X,
} from "lucide-react";

// ============================================================================
// LIVE METRICS PANEL
// ============================================================================

interface LiveMetricsPanelProps {
  transactions: TransactionWithPrediction[];
  isRunning: boolean;
  elapsedTime: number;
}

function LiveMetricsPanel({ transactions, isRunning, elapsedTime }: LiveMetricsPanelProps) {
  const stats = useMemo(() => ({
    totalTxns: transactions.length,
    fraudDetected: transactions.filter((t) => t.prediction?.is_fraud).length,
    blocked: transactions.filter((t) => t.prediction?.action_taken === "BLOCK").length,
    mfa: transactions.filter((t) => t.prediction?.action_taken === "MFA").length,
    avgLatency: transactions.length > 0
      ? transactions.reduce((acc, t) => acc + (t.prediction?.processing_time_ms ?? 0), 0) / transactions.length
      : 0,
    blockedAmount: transactions
      .filter((t) => t.prediction?.action_taken === "BLOCK")
      .reduce((acc, t) => acc + t.amount, 0),
    detectionRate: transactions.length > 0
      ? (transactions.filter((t) => t.prediction?.is_fraud).length / transactions.length) * 100
      : 0,
  }), [transactions]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const MetricBox = ({ value, label, color = "#f0f4f8" }: { value: string | number; label: string; color?: string }) => (
    <div className="text-center p-4">
      <div className="text-2xl font-semibold font-mono tracking-tight" style={{ color }}>
        {value}
      </div>
      <div className="text-[9px] font-mono uppercase tracking-[0.1em] text-[#64748b] mt-1">
        {label}
      </div>
    </div>
  );

  return (
    <div className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[14px] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-[#38bdf8]" />
          <span className="text-[13px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Live Metrics
          </span>
        </div>
        {isRunning && (
          <div className="flex items-center gap-2 text-[11px] font-mono text-[#38bdf8]">
            <Clock className="w-3 h-3" />
            {formatTime(elapsedTime)}
          </div>
        )}
      </div>

      <div className="grid grid-cols-4 divide-x divide-[rgba(148,163,184,0.08)]">
        <MetricBox value={stats.totalTxns} label="Total TXNs" color="#38bdf8" />
        <MetricBox value={stats.fraudDetected} label="Fraud Found" color="#f87171" />
        <MetricBox value={stats.blocked} label="Blocked" color="#fbbf24" />
        <MetricBox value={stats.mfa} label="MFA Sent" color="#38bdf8" />
      </div>
      
      <div className="grid grid-cols-3 divide-x divide-[rgba(148,163,184,0.08)] border-t border-[rgba(148,163,184,0.08)]">
        <MetricBox 
          value={`${stats.avgLatency.toFixed(0)}ms`} 
          label="Avg Latency" 
          color="#34d399" 
        />
        <MetricBox 
          value={`${stats.detectionRate.toFixed(1)}%`} 
          label="Detection Rate" 
          color={stats.detectionRate >= 80 ? "#f87171" : stats.detectionRate >= 50 ? "#fbbf24" : "#34d399"} 
        />
        <MetricBox 
          value={`$${stats.blockedAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} 
          label="Blocked $" 
          color="#f87171" 
        />
      </div>
    </div>
  );
}

// ============================================================================
// MAIN SIMULATOR PAGE
// ============================================================================

export default function SimulatorPage() {
  const [selectedScenario, setSelectedScenario] = useState<AttackScenario>("normal");
  const [isSimulatorRunning, setIsSimulatorRunning] = useState(false);
  const [activeScenario, setActiveScenario] = useState<AttackScenario | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [selectedTransaction, setSelectedTransaction] = useState<TransactionWithPrediction | null>(null);

  const {
    transactions,
    alerts,
    isConnected,
    isReconnecting,
    attackActive,
    connect,
    injectAttack,
    stopAttack,
    clearTransactions,
  } = useTransactionStream({
    maxTransactions: 200,
    autoReconnect: true,
  });

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSimulatorRunning) {
      interval = setInterval(() => setElapsedTime((prev) => prev + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isSimulatorRunning]);

  // Sync attack status - using refs to avoid the setState-in-effect issue
  const isSimRunningRef = useRef(isSimulatorRunning);
  isSimRunningRef.current = isSimulatorRunning;

  useEffect(() => {
    if (attackActive && !isSimRunningRef.current) {
      setIsSimulatorRunning(true);
      setActiveScenario(attackActive as AttackScenario);
    } else if (!attackActive && isSimRunningRef.current) {
      setIsSimulatorRunning(false);
    }
  }, [attackActive]);

  const handleStart = useCallback(
    (config: { scenario: AttackScenario; intensity: AttackIntensity; duration: number; transactionsPerSecond: number }) => {
      setIsSimulatorRunning(true);
      setActiveScenario(config.scenario);
      setElapsedTime(0);
      clearTransactions();
      injectAttack(config.scenario, config.duration);
    },
    [injectAttack, clearTransactions]
  );

  const handleStop = useCallback(() => {
    setIsSimulatorRunning(false);
    setActiveScenario(null);
    stopAttack();
  }, [stopAttack]);

  const handleReset = useCallback(() => {
    setIsSimulatorRunning(false);
    setActiveScenario(null);
    setElapsedTime(0);
    clearTransactions();
    stopAttack();
  }, [clearTransactions, stopAttack]);

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      <FloatingHeader />

      <main className="pt-20 px-6 pb-8">
        <div className="max-w-[1800px] mx-auto">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-[rgba(251,191,36,0.1)] border border-[rgba(251,191,36,0.2)]">
                <Beaker className="w-6 h-6 text-[#fbbf24]" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-[#f0f4f8] tracking-tight" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  Attack Simulator
                </h1>
                <p className="text-[13px] text-[#64748b]">
                  Inject attack scenarios to test fraud detection
                </p>
              </div>
            </div>

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
                    <span>Connected</span>
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

              {!isConnected && (
                <button
                  onClick={connect}
                  className="px-4 py-1.5 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] text-[#38bdf8] text-[12px] font-medium hover:bg-[rgba(56,189,248,0.15)] transition-all"
                >
                  Connect
                </button>
              )}
            </div>
          </div>

          {/* Warning Banner */}
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 px-4 py-3 mb-6 bg-[rgba(251,191,36,0.06)] border border-[rgba(251,191,36,0.15)] rounded-xl"
          >
            <AlertTriangle className="w-5 h-5 text-[#fbbf24] flex-shrink-0" />
            <div className="flex-1">
              <p className="text-[13px] font-medium text-[#fbbf24]">Simulation Environment</p>
              <p className="text-[12px] text-[#fbbf24]/70 mt-0.5">
                All transactions are synthetic test data. Use this to validate ML model responses.
              </p>
            </div>
            <a
              href="/dashboard"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[rgba(251,191,36,0.25)] text-[#fbbf24] text-[11px] font-medium hover:bg-[rgba(251,191,36,0.08)] transition-all"
            >
              Dashboard
              <ExternalLink className="w-3 h-3" />
            </a>
          </motion.div>

          {/* Attack Scenario Selection */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Target className="w-4 h-4 text-[#38bdf8]" />
              <h2 className="text-[15px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Select Attack Scenario
              </h2>
            </div>
            <AttackScenarioGrid
              selectedScenario={selectedScenario}
              activeScenario={activeScenario}
              onSelectScenario={setSelectedScenario}
            />
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-5 space-y-6">
              <SimulatorControls
                selectedScenario={selectedScenario}
                isRunning={isSimulatorRunning}
                onStart={handleStart}
                onStop={handleStop}
                onReset={handleReset}
              />
              <LiveMetricsPanel
                transactions={transactions}
                isRunning={isSimulatorRunning}
                elapsedTime={elapsedTime}
              />
            </div>

            {/* Right Column - Live Feed */}
            <div className="lg:col-span-7">
              <div className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[14px] overflow-hidden h-[600px] flex flex-col">
                <div className="flex items-center justify-between px-4 py-3 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-[#fbbf24]" />
                    <span className="text-[13px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      Injection Feed
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] font-mono">
                    <span className="text-[#38bdf8]">{transactions.length} total</span>
                    <span className="text-[#f87171]">{transactions.filter(t => t.prediction?.is_fraud).length} fraud</span>
                  </div>
                </div>
                <LiveInjectionFeed
                  transactions={transactions}
                  attackScenario={activeScenario}
                  isRunning={isSimulatorRunning}
                  maxDisplay={50}
                  onInspect={setSelectedTransaction}
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 flex items-center justify-between px-5 py-3.5 bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-[10px]">
            <div className="flex items-center gap-6 text-[11px] font-mono text-[#64748b]">
              <div className="flex items-center gap-2">
                <Activity className="w-3.5 h-3.5" />
                {transactions.length} in buffer
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-3.5 h-3.5" />
                {alerts.length} alerts
              </div>
              <div className="flex items-center gap-2">
                <Zap className="w-3.5 h-3.5" />
                ML: {isConnected ? <span className="text-[#34d399]">Online</span> : <span className="text-[#f87171]">Offline</span>}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={clearTransactions}
                className="flex items-center gap-2 px-4 py-2 rounded-md border border-[rgba(148,163,184,0.12)] text-[12px] font-medium text-[#94a3b8] hover:bg-[#1a222d] hover:text-[#f0f4f8] transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Clear
              </button>
              <a
                href="/dashboard"
                className="flex items-center gap-2 px-4 py-2 rounded-md bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] text-[#38bdf8] text-[12px] font-medium hover:bg-[rgba(56,189,248,0.15)] transition-all"
              >
                Dashboard
                <ChevronRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>
      </main>

      {/* Transaction Modal */}
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
                  <p className="text-[12px] font-mono text-[#64748b]">{selectedTransaction.txn_id}</p>
                </div>
                <button
                  onClick={() => setSelectedTransaction(null)}
                  className="p-1.5 rounded-md hover:bg-[#1a222d] text-[#64748b] hover:text-[#f0f4f8] transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-5">
                <div className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">Amount</div>
                  <div className="text-[14px] font-medium text-[#f0f4f8]">${selectedTransaction.amount.toLocaleString()}</div>
                </div>
                <div className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">Risk Score</div>
                  <div 
                    className="text-[14px] font-semibold"
                    style={{
                      color: (selectedTransaction.prediction?.risk_score ?? 0) >= 70 ? "#f87171" 
                           : (selectedTransaction.prediction?.risk_score ?? 0) >= 40 ? "#fbbf24" 
                           : "#34d399"
                    }}
                  >
                    {selectedTransaction.prediction?.risk_score?.toFixed(0) ?? 0}%
                  </div>
                </div>
                <div className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">Merchant</div>
                  <div className="text-[14px] text-[#f0f4f8]">{selectedTransaction.merchant}</div>
                </div>
                <div className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">Location</div>
                  <div className="text-[14px] text-[#f0f4f8]">{selectedTransaction.location}</div>
                </div>
                <div className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">Fraud Type</div>
                  <div className="text-[14px] text-[#fbbf24]">
                    {selectedTransaction.prediction?.fraud_type?.replace("_", " ") || "N/A"}
                  </div>
                </div>
                <div className="bg-[#0f1419] rounded-lg p-3 border border-[rgba(148,163,184,0.06)]">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-1">Action</div>
                  <div 
                    className="text-[14px] font-semibold"
                    style={{
                      color: selectedTransaction.prediction?.action_taken === "BLOCK" ? "#f87171" 
                           : selectedTransaction.prediction?.action_taken === "MFA" ? "#fbbf24" 
                           : "#34d399"
                    }}
                  >
                    {selectedTransaction.prediction?.action_taken || "N/A"}
                  </div>
                </div>
              </div>

              {/* SHAP Values */}
              {selectedTransaction.prediction?.shap_values && (
                <div className="bg-[#0f1419] rounded-lg p-4 border border-[rgba(148,163,184,0.06)] mb-5">
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#64748b] mb-3">
                    Contributing Factors
                  </div>
                  <div className="space-y-2">
                    {Object.entries(selectedTransaction.prediction.shap_values)
                      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                      .slice(0, 5)
                      .map(([feature, value]) => (
                        <div key={feature} className="flex items-center gap-3">
                          <div className="w-24 text-[11px] font-mono text-[#64748b] truncate">{feature}</div>
                          <div className="flex-1 h-1.5 bg-[#1a222d] rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all"
                              style={{
                                width: `${Math.min(Math.abs(value) * 100, 100)}%`,
                                backgroundColor: value > 0 ? "#f87171" : "#34d399",
                              }}
                            />
                          </div>
                          <div
                            className="w-14 text-[11px] font-mono text-right"
                            style={{ color: value > 0 ? "#f87171" : "#34d399" }}
                          >
                            {value > 0 ? "+" : ""}{(value * 100).toFixed(1)}%
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <a
                  href={`/investigation/${selectedTransaction.txn_id}`}
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] text-[#38bdf8] text-[13px] font-medium hover:bg-[rgba(56,189,248,0.15)] transition-all"
                >
                  Full Investigation
                  <ChevronRight className="w-4 h-4" />
                </a>
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
