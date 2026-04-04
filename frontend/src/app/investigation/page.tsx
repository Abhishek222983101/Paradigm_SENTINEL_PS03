// ============================================================================
// SENTINEL INVESTIGATION HUB - List View
// Browse and search flagged transactions for deep investigation
// ============================================================================

"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { FloatingHeader } from "@/components/layout";
import {
  Search,
  Filter,
  AlertTriangle,
  Shield,
  ShieldAlert,
  Clock,
  ChevronRight,
  Eye,
  TrendingUp,
  DollarSign,
  MapPin,
  User,
  Fingerprint,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================================
// TYPES
// ============================================================================

interface FlaggedTransaction {
  txn_id: string;
  timestamp: string;
  amount: number;
  currency: string;
  merchant: string;
  user_id: string;
  location: string;
  risk_score: number;
  fraud_type: string;
  status: "pending" | "investigating" | "resolved" | "dismissed";
  action_taken: string;
}

// ============================================================================
// MOCK DATA - Replace with API call
// ============================================================================

const mockFlaggedTransactions: FlaggedTransaction[] = [
  {
    txn_id: "TXN-20260404-AX8K2M",
    timestamp: "2026-04-04T14:22:00Z",
    amount: 15420.00,
    currency: "USD",
    merchant: "Luxury Electronics Ltd",
    user_id: "USR-4421",
    location: "Lagos, Nigeria",
    risk_score: 94,
    fraud_type: "ACCOUNT_TAKEOVER",
    status: "pending",
    action_taken: "BLOCK",
  },
  {
    txn_id: "TXN-20260404-BK3L9P",
    timestamp: "2026-04-04T13:45:00Z",
    amount: 2.50,
    currency: "USD",
    merchant: "Test Merchant #1",
    user_id: "USR-7892",
    location: "Unknown VPN",
    risk_score: 88,
    fraud_type: "CARD_TESTING",
    status: "investigating",
    action_taken: "BLOCK",
  },
  {
    txn_id: "TXN-20260404-CM5N7R",
    timestamp: "2026-04-04T12:30:00Z",
    amount: 8750.00,
    currency: "USD",
    merchant: "Crypto Exchange Pro",
    user_id: "USR-1156",
    location: "Multiple Locations",
    risk_score: 91,
    fraud_type: "FRAUD_RING",
    status: "pending",
    action_taken: "MFA",
  },
  {
    txn_id: "TXN-20260404-DN8P2S",
    timestamp: "2026-04-04T11:15:00Z",
    amount: 3200.00,
    currency: "USD",
    merchant: "Premium Goods Store",
    user_id: "USR-NEW-001",
    location: "Miami, FL",
    risk_score: 76,
    fraud_type: "SYNTHETIC_IDENTITY",
    status: "resolved",
    action_taken: "BLOCK",
  },
  {
    txn_id: "TXN-20260404-EP1Q4T",
    timestamp: "2026-04-04T10:00:00Z",
    amount: 45000.00,
    currency: "USD",
    merchant: "Wire Transfer Service",
    user_id: "USR-8834",
    location: "Cayman Islands",
    risk_score: 97,
    fraud_type: "MONEY_MULE",
    status: "pending",
    action_taken: "BLOCK",
  },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const fraudTypeLabels: Record<string, { label: string; color: string }> = {
  ACCOUNT_TAKEOVER: { label: "Account Takeover", color: "#f87171" },
  CARD_TESTING: { label: "Card Testing", color: "#fbbf24" },
  FRAUD_RING: { label: "Fraud Ring", color: "#f87171" },
  SYNTHETIC_IDENTITY: { label: "Synthetic ID", color: "#a78bfa" },
  MONEY_MULE: { label: "Money Mule", color: "#fb923c" },
};

const statusStyles: Record<string, { bg: string; text: string }> = {
  pending: { bg: "rgba(251,191,36,0.15)", text: "#fbbf24" },
  investigating: { bg: "rgba(56,189,248,0.15)", text: "#38bdf8" },
  resolved: { bg: "rgba(52,211,153,0.15)", text: "#34d399" },
  dismissed: { bg: "rgba(100,116,139,0.15)", text: "#64748b" },
};

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function formatDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

// ============================================================================
// INVESTIGATION CARD COMPONENT
// ============================================================================

function InvestigationCard({ txn }: { txn: FlaggedTransaction }) {
  const fraudInfo = fraudTypeLabels[txn.fraud_type] || { label: txn.fraud_type, color: "#64748b" };
  const status = statusStyles[txn.status];
  const isCritical = txn.risk_score >= 90;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.2 }}
    >
      <Link href={`/investigation/${txn.txn_id}`}>
        <div
          className={cn(
            "group relative bg-[#151b23] border rounded-xl p-5 cursor-pointer transition-all duration-200",
            "hover:bg-[#1a222d] hover:border-[rgba(56,189,248,0.3)]",
            isCritical
              ? "border-[rgba(248,113,113,0.3)] border-l-[3px] border-l-[#f87171]"
              : "border-[rgba(148,163,184,0.1)] border-l-[3px] border-l-[#fbbf24]"
          )}
        >
          {/* Critical Badge */}
          {isCritical && (
            <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2 py-1 bg-[rgba(248,113,113,0.15)] rounded-full">
              <span className="w-1.5 h-1.5 bg-[#f87171] rounded-full animate-pulse" />
              <span className="text-[10px] font-mono font-semibold text-[#f87171] uppercase">Critical</span>
            </div>
          )}

          {/* Header Row */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[#38bdf8] font-mono text-sm font-medium">{txn.txn_id}</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-[#64748b]">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {formatDate(txn.timestamp)} {formatTime(txn.timestamp)}
                </span>
                <span
                  className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase"
                  style={{ backgroundColor: status.bg, color: status.text }}
                >
                  {txn.status}
                </span>
              </div>
            </div>

            {/* Risk Score */}
            <div
              className={cn(
                "text-center px-3 py-2 rounded-lg font-mono",
                txn.risk_score >= 90
                  ? "bg-[rgba(248,113,113,0.15)] text-[#f87171]"
                  : txn.risk_score >= 70
                  ? "bg-[rgba(251,191,36,0.15)] text-[#fbbf24]"
                  : "bg-[rgba(52,211,153,0.15)] text-[#34d399]"
              )}
            >
              <div className="text-2xl font-bold">{txn.risk_score}</div>
              <div className="text-[9px] uppercase tracking-wider opacity-70">Risk</div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div>
              <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Amount</div>
              <div className="text-sm font-semibold text-[#f0f4f8]">
                ${txn.amount.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Merchant</div>
              <div className="text-sm text-[#f0f4f8] truncate">{txn.merchant}</div>
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Location</div>
              <div className="text-sm text-[#f0f4f8] truncate">{txn.location}</div>
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">User</div>
              <div className="text-sm text-[#f0f4f8] font-mono">{txn.user_id}</div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-[rgba(148,163,184,0.08)]">
            <div className="flex items-center gap-2">
              <span
                className="px-2 py-1 rounded text-[10px] font-mono font-medium"
                style={{ backgroundColor: `${fraudInfo.color}20`, color: fraudInfo.color }}
              >
                {fraudInfo.label}
              </span>
              <span
                className={cn(
                  "px-2 py-1 rounded text-[10px] font-mono font-medium",
                  txn.action_taken === "BLOCK"
                    ? "bg-[rgba(248,113,113,0.15)] text-[#f87171]"
                    : "bg-[rgba(251,191,36,0.15)] text-[#fbbf24]"
                )}
              >
                {txn.action_taken}
              </span>
            </div>
            <div className="flex items-center gap-2 text-[#38bdf8] text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              <Eye className="w-4 h-4" />
              Investigate
              <ChevronRight className="w-4 h-4" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function InvestigationPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [transactions, setTransactions] = useState<FlaggedTransaction[]>(mockFlaggedTransactions);
  const [isLoading, setIsLoading] = useState(false);

  const filteredTransactions = transactions.filter((txn) => {
    const matchesSearch =
      txn.txn_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.merchant.toLowerCase().includes(searchQuery.toLowerCase()) ||
      txn.user_id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === "all" || txn.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const stats = {
    total: transactions.length,
    pending: transactions.filter((t) => t.status === "pending").length,
    critical: transactions.filter((t) => t.risk_score >= 90).length,
    totalAmount: transactions.reduce((acc, t) => acc + t.amount, 0),
  };

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      <FloatingHeader />

      <main className="pt-20 px-6 pb-8">
        <div className="max-w-[1400px] mx-auto">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.2)]">
                <Search className="w-6 h-6 text-[#38bdf8]" />
              </div>
              <div>
                <h1
                  className="text-2xl font-semibold text-[#f0f4f8] tracking-tight"
                  style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                >
                  Investigation Hub
                </h1>
                <p className="text-[13px] text-[#64748b]">
                  Deep-dive into flagged transactions and fraud patterns
                </p>
              </div>
            </div>

            <button
              onClick={() => setIsLoading(true)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] text-[#38bdf8] text-sm font-medium hover:bg-[rgba(56,189,248,0.15)] transition-all"
            >
              <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
              Refresh
            </button>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[
              { label: "Total Flagged", value: stats.total, icon: <ShieldAlert className="w-5 h-5" />, color: "#38bdf8" },
              { label: "Pending Review", value: stats.pending, icon: <Clock className="w-5 h-5" />, color: "#fbbf24" },
              { label: "Critical", value: stats.critical, icon: <AlertTriangle className="w-5 h-5" />, color: "#f87171" },
              { label: "Total Amount", value: `$${stats.totalAmount.toLocaleString()}`, icon: <DollarSign className="w-5 h-5" />, color: "#34d399" },
            ].map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-xl p-4"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="p-2 rounded-lg"
                    style={{ backgroundColor: `${stat.color}15`, color: stat.color }}
                  >
                    {stat.icon}
                  </div>
                  <div>
                    <div className="text-[10px] font-mono uppercase text-[#64748b]">{stat.label}</div>
                    <div className="text-xl font-bold text-[#f0f4f8]">{stat.value}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Search & Filter Bar */}
          <div className="flex items-center gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
              <input
                type="text"
                placeholder="Search by Transaction ID, Merchant, or User..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-[#151b23] border border-[rgba(148,163,184,0.1)] rounded-xl text-[#f0f4f8] text-sm placeholder:text-[#64748b] focus:outline-none focus:border-[rgba(56,189,248,0.4)] transition-colors"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-[#64748b]" />
              {["all", "pending", "investigating", "resolved"].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-xs font-medium transition-all",
                    filterStatus === status
                      ? "bg-[rgba(56,189,248,0.15)] text-[#38bdf8] border border-[rgba(56,189,248,0.3)]"
                      : "bg-[#151b23] text-[#64748b] border border-[rgba(148,163,184,0.1)] hover:border-[rgba(148,163,184,0.2)]"
                  )}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Transaction List */}
          <div className="space-y-4">
            {filteredTransactions.length > 0 ? (
              filteredTransactions.map((txn) => (
                <InvestigationCard key={txn.txn_id} txn={txn} />
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-[#64748b]">
                <Shield className="w-12 h-12 mb-4 opacity-30" />
                <div className="text-sm font-mono">No transactions match your filters</div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
