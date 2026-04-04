// ============================================================================
// SENTINEL INVESTIGATION DETAIL PAGE
// Deep-dive into a specific flagged transaction
// ============================================================================

"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import { FloatingHeader } from "@/components/layout";
import { SHAPChart, InvestigationReport, ActionConsole } from "@/components/investigation";
import {
  ArrowLeft,
  Shield,
  ShieldAlert,
  Clock,
  MapPin,
  Smartphone,
  User,
  DollarSign,
  CreditCard,
  Globe,
  Fingerprint,
  Activity,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
  Network,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================================
// TYPES
// ============================================================================

interface TransactionDetail {
  txn_id: string;
  timestamp: string;
  amount: number;
  currency: string;
  merchant: string;
  merchant_category: string;
  user_id: string;
  location: string;
  device_id: string;
  ip_address: string;
  risk_score: number;
  fraud_type: string;
  status: string;
  action_taken: string;
  shap_values: Record<string, number>;
  user_profile: {
    account_age_days: number;
    avg_transaction: number;
    total_transactions: number;
    risk_level: string;
  };
  related_alerts: number;
}

// ============================================================================
// MOCK DATA
// ============================================================================

const mockTransactionDetail: TransactionDetail = {
  txn_id: "TXN-20260404-AX8K2M",
  timestamp: "2026-04-04T14:22:00Z",
  amount: 15420.0,
  currency: "USD",
  merchant: "Luxury Electronics Ltd",
  merchant_category: "Electronics Store",
  user_id: "USR-4421",
  location: "Lagos, Nigeria",
  device_id: "DEV-NEW-X892",
  ip_address: "197.210.XX.XX",
  risk_score: 94,
  fraud_type: "ACCOUNT_TAKEOVER",
  status: "pending",
  action_taken: "BLOCK",
  shap_values: {
    amount: 0.45,
    location: 0.30,
    device: 0.25,
    velocity: 0.18,
    time_of_day: -0.05,
    merchant: 0.12,
    user_history: -0.08,
    ip_risk: 0.22,
  },
  user_profile: {
    account_age_days: 847,
    avg_transaction: 156.42,
    total_transactions: 342,
    risk_level: "LOW",
  },
  related_alerts: 3,
};

// ============================================================================
// INFO CARD COMPONENT
// ============================================================================

function InfoCard({
  icon,
  label,
  value,
  subValue,
  color = "#38bdf8",
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subValue?: string;
  color?: string;
}) {
  return (
    <div className="bg-[#0f1419] rounded-xl p-4 border border-[rgba(148,163,184,0.06)]">
      <div className="flex items-center gap-2 mb-2">
        <div style={{ color }} className="opacity-70">
          {icon}
        </div>
        <span className="text-[10px] font-mono uppercase text-[#64748b]">{label}</span>
      </div>
      <div className="text-lg font-semibold text-[#f0f4f8]" style={{ color: typeof value === 'number' && value > 80 ? '#f87171' : undefined }}>
        {value}
      </div>
      {subValue && <div className="text-[11px] text-[#64748b] mt-1">{subValue}</div>}
    </div>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function InvestigationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const txnId = params.txn_id as string;

  const [transaction, setTransaction] = useState<TransactionDetail | null>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API fetch
    const fetchTransaction = async () => {
      setIsLoading(true);
      await new Promise((resolve) => setTimeout(resolve, 500));
      // In production, fetch from API based on txnId
      setTransaction({ ...mockTransactionDetail, txn_id: txnId });
      setIsLoading(false);
      // Auto-trigger report generation
      setTimeout(() => setIsGeneratingReport(true), 1000);
    };

    fetchTransaction();
  }, [txnId]);

  const handleAction = (action: string, notes?: string) => {
    console.log("Action executed:", action, notes);
    // In production, call API
  };

  const handleRegenerateReport = () => {
    setIsGeneratingReport(true);
  };

  if (isLoading || !transaction) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        >
          <Shield className="w-8 h-8 text-[#38bdf8]" />
        </motion.div>
      </div>
    );
  }

  const isCritical = transaction.risk_score >= 90;

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      <FloatingHeader />

      <main className="pt-20 px-6 pb-8">
        <div className="max-w-[1600px] mx-auto">
          {/* Back Navigation */}
          <Link
            href="/investigation"
            className="inline-flex items-center gap-2 text-[#64748b] hover:text-[#f0f4f8] text-sm mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Investigation Hub
          </Link>

          {/* Page Header */}
          <div className="flex items-start justify-between mb-8">
            <div className="flex items-center gap-4">
              <div
                className={cn(
                  "p-3 rounded-xl border",
                  isCritical
                    ? "bg-[rgba(248,113,113,0.1)] border-[rgba(248,113,113,0.2)]"
                    : "bg-[rgba(251,191,36,0.1)] border-[rgba(251,191,36,0.2)]"
                )}
              >
                <ShieldAlert className={cn("w-6 h-6", isCritical ? "text-[#f87171]" : "text-[#fbbf24]")} />
              </div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1
                    className="text-xl font-semibold text-[#f0f4f8] tracking-tight font-mono"
                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                  >
                    {transaction.txn_id}
                  </h1>
                  {isCritical && (
                    <span className="flex items-center gap-1.5 px-2 py-1 bg-[rgba(248,113,113,0.15)] rounded-full">
                      <span className="w-1.5 h-1.5 bg-[#f87171] rounded-full animate-pulse" />
                      <span className="text-[10px] font-mono font-semibold text-[#f87171] uppercase">
                        Critical
                      </span>
                    </span>
                  )}
                </div>
                <p className="text-[13px] text-[#64748b]">
                  {new Date(transaction.timestamp).toLocaleString()} • {transaction.fraud_type.replace("_", " ")}
                </p>
              </div>
            </div>

            {/* Risk Score Badge */}
            <div
              className={cn(
                "text-center px-6 py-4 rounded-xl font-mono",
                isCritical
                  ? "bg-[rgba(248,113,113,0.15)] border border-[rgba(248,113,113,0.3)]"
                  : "bg-[rgba(251,191,36,0.15)] border border-[rgba(251,191,36,0.3)]"
              )}
            >
              <div className={cn("text-4xl font-bold", isCritical ? "text-[#f87171]" : "text-[#fbbf24]")}>
                {transaction.risk_score}
              </div>
              <div className="text-[10px] uppercase tracking-wider text-[#64748b] mt-1">Risk Score</div>
            </div>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-12 gap-6">
            {/* Left Column - Transaction Details */}
            <div className="col-span-8 space-y-6">
              {/* Transaction Info Grid */}
              <div className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-xl p-5">
                <h2 className="text-sm font-semibold text-[#f0f4f8] mb-4" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  Transaction Details
                </h2>
                <div className="grid grid-cols-4 gap-4">
                  <InfoCard
                    icon={<DollarSign className="w-4 h-4" />}
                    label="Amount"
                    value={`$${transaction.amount.toLocaleString()}`}
                    color="#f87171"
                  />
                  <InfoCard
                    icon={<CreditCard className="w-4 h-4" />}
                    label="Merchant"
                    value={transaction.merchant}
                    subValue={transaction.merchant_category}
                  />
                  <InfoCard
                    icon={<MapPin className="w-4 h-4" />}
                    label="Location"
                    value={transaction.location}
                    color="#fbbf24"
                  />
                  <InfoCard
                    icon={<Clock className="w-4 h-4" />}
                    label="Time"
                    value={new Date(transaction.timestamp).toLocaleTimeString()}
                    subValue={new Date(transaction.timestamp).toLocaleDateString()}
                  />
                  <InfoCard
                    icon={<User className="w-4 h-4" />}
                    label="User ID"
                    value={transaction.user_id}
                    subValue={`${transaction.user_profile.total_transactions} total txns`}
                  />
                  <InfoCard
                    icon={<Smartphone className="w-4 h-4" />}
                    label="Device"
                    value={transaction.device_id}
                    subValue="New Device"
                    color="#f87171"
                  />
                  <InfoCard
                    icon={<Globe className="w-4 h-4" />}
                    label="IP Address"
                    value={transaction.ip_address}
                    subValue="High Risk Region"
                    color="#fbbf24"
                  />
                  <InfoCard
                    icon={<Activity className="w-4 h-4" />}
                    label="Action Taken"
                    value={transaction.action_taken}
                    color={transaction.action_taken === "BLOCK" ? "#f87171" : "#fbbf24"}
                  />
                </div>
              </div>

              {/* SHAP Analysis */}
              <SHAPChart shapValues={transaction.shap_values} baseScore={50} />

              {/* AI Report */}
              <InvestigationReport
                txnId={transaction.txn_id}
                isGenerating={isGeneratingReport}
                onRegenerate={handleRegenerateReport}
              />
            </div>

            {/* Right Column - Actions & User Profile */}
            <div className="col-span-4 space-y-6">
              {/* Action Console */}
              <ActionConsole
                txnId={transaction.txn_id}
                currentStatus={transaction.status}
                onAction={handleAction}
              />

              {/* User Profile Card */}
              <div className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-xl overflow-hidden">
                <div className="px-5 py-4 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
                  <div className="flex items-center gap-2">
                    <Fingerprint className="w-4 h-4 text-[#38bdf8]" />
                    <h3 className="text-[14px] font-semibold text-[#f0f4f8]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      User Profile
                    </h3>
                  </div>
                </div>
                <div className="p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#64748b]">Account Age</span>
                    <span className="text-sm font-mono text-[#f0f4f8]">
                      {transaction.user_profile.account_age_days} days
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#64748b]">Avg Transaction</span>
                    <span className="text-sm font-mono text-[#f0f4f8]">
                      ${transaction.user_profile.avg_transaction.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#64748b]">Total Transactions</span>
                    <span className="text-sm font-mono text-[#f0f4f8]">
                      {transaction.user_profile.total_transactions}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-[#64748b]">Historical Risk</span>
                    <span className="text-sm font-mono text-[#34d399]">
                      {transaction.user_profile.risk_level}
                    </span>
                  </div>
                  <div className="pt-3 border-t border-[rgba(148,163,184,0.08)]">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-[#64748b]">Related Alerts</span>
                      <span className="text-sm font-mono text-[#f87171]">
                        {transaction.related_alerts} active
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Links */}
              <div className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-xl p-5">
                <h3 className="text-[14px] font-semibold text-[#f0f4f8] mb-4" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  Quick Actions
                </h3>
                <div className="space-y-2">
                  <Link
                    href={`/graph?user=${transaction.user_id}`}
                    className="flex items-center justify-between p-3 rounded-lg bg-[#0f1419] border border-[rgba(148,163,184,0.06)] hover:border-[rgba(56,189,248,0.3)] transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <Network className="w-4 h-4 text-[#38bdf8]" />
                      <span className="text-sm text-[#f0f4f8]">View Fraud Graph</span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-[#64748b] group-hover:text-[#38bdf8] transition-colors" />
                  </Link>
                  <Link
                    href="/dashboard"
                    className="flex items-center justify-between p-3 rounded-lg bg-[#0f1419] border border-[rgba(148,163,184,0.06)] hover:border-[rgba(56,189,248,0.3)] transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <Activity className="w-4 h-4 text-[#34d399]" />
                      <span className="text-sm text-[#f0f4f8]">Back to Dashboard</span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-[#64748b] group-hover:text-[#38bdf8] transition-colors" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
