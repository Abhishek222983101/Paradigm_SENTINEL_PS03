// ============================================================================
// SENTINEL ATTACK SCENARIO CARD
// Refined Attack Type Selector
// ============================================================================

"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AttackScenario } from "@/types";
import {
  UserX,
  CreditCard,
  Network,
  Fingerprint,
  Activity,
} from "lucide-react";

// ============================================================================
// ATTACK SCENARIO CONFIGURATIONS
// ============================================================================

export interface AttackScenarioConfig {
  id: AttackScenario;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: "danger" | "warning" | "primary" | "success";
  stats: {
    avgRiskScore: string;
    detectionRate: string;
    avgAmount: string;
  };
  indicators: string[];
}

const colorMap = {
  danger: {
    accent: "#f87171",
    bg: "rgba(248, 113, 113, 0.08)",
    border: "rgba(248, 113, 113, 0.3)",
    glow: "0 0 20px rgba(248, 113, 113, 0.15)",
  },
  warning: {
    accent: "#fbbf24",
    bg: "rgba(251, 191, 36, 0.08)",
    border: "rgba(251, 191, 36, 0.3)",
    glow: "0 0 20px rgba(251, 191, 36, 0.15)",
  },
  primary: {
    accent: "#38bdf8",
    bg: "rgba(56, 189, 248, 0.08)",
    border: "rgba(56, 189, 248, 0.3)",
    glow: "0 0 20px rgba(56, 189, 248, 0.15)",
  },
  success: {
    accent: "#34d399",
    bg: "rgba(52, 211, 153, 0.08)",
    border: "rgba(52, 211, 153, 0.3)",
    glow: "0 0 20px rgba(52, 211, 153, 0.15)",
  },
};

export const attackScenarios: AttackScenarioConfig[] = [
  {
    id: "normal",
    name: "Normal Traffic",
    description: "Standard transaction flow with ~5% natural fraud occurrence",
    icon: <Activity className="w-5 h-5" />,
    color: "success",
    stats: {
      avgRiskScore: "15-25",
      detectionRate: "98.5%",
      avgAmount: "$50-500",
    },
    indicators: [
      "Regular purchase patterns",
      "Known device fingerprints",
      "Consistent geolocations",
      "Normal velocity",
    ],
  },
  {
    id: "account_takeover",
    name: "Account Takeover",
    description: "Simulates credential compromise with unusual login patterns",
    icon: <UserX className="w-5 h-5" />,
    color: "danger",
    stats: {
      avgRiskScore: "75-95",
      detectionRate: "94.2%",
      avgAmount: "$500-5000",
    },
    indicators: [
      "New device fingerprint",
      "Unusual location/IP",
      "Rapid transactions",
      "Password changes",
    ],
  },
  {
    id: "card_testing",
    name: "Card Testing",
    description: "Rapid micro-transactions to validate stolen card numbers",
    icon: <CreditCard className="w-5 h-5" />,
    color: "warning",
    stats: {
      avgRiskScore: "65-85",
      detectionRate: "97.8%",
      avgAmount: "$0.50-5.00",
    },
    indicators: [
      "Multiple small transactions",
      "High velocity (>20/min)",
      "Sequential card numbers",
      "Same merchant category",
    ],
  },
  {
    id: "fraud_ring",
    name: "Fraud Ring",
    description: "Coordinated attack from multiple linked accounts",
    icon: <Network className="w-5 h-5" />,
    color: "danger",
    stats: {
      avgRiskScore: "80-95",
      detectionRate: "89.3%",
      avgAmount: "$1000-10000",
    },
    indicators: [
      "Shared device IDs",
      "Common IP addresses",
      "Inter-account transfers",
      "Synchronized timing",
    ],
  },
  {
    id: "synthetic_identity",
    name: "Synthetic Identity",
    description: "Fabricated identities using mixed real/fake data",
    icon: <Fingerprint className="w-5 h-5" />,
    color: "warning",
    stats: {
      avgRiskScore: "55-75",
      detectionRate: "82.1%",
      avgAmount: "$200-2000",
    },
    indicators: [
      "No credit history",
      "Mismatched SSN/Name",
      "Recently created accounts",
      "Thin file profiles",
    ],
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

interface AttackScenarioCardProps {
  scenario: AttackScenarioConfig;
  isSelected: boolean;
  isActive: boolean;
  onSelect: () => void;
  className?: string;
}

export function AttackScenarioCard({
  scenario,
  isSelected,
  isActive,
  onSelect,
  className,
}: AttackScenarioCardProps) {
  const colors = colorMap[scenario.color];

  return (
    <motion.button
      onClick={onSelect}
      className={cn(
        "relative w-full text-left rounded-[14px] p-5 transition-all duration-200",
        "bg-[#151b23] border",
        isSelected
          ? "border-[rgba(56,189,248,0.4)]"
          : "border-[rgba(148,163,184,0.08)] hover:border-[rgba(148,163,184,0.15)]",
        isActive && "animate-pulse",
        className
      )}
      style={{
        borderColor: isSelected ? colors.border : undefined,
        background: isSelected 
          ? `linear-gradient(180deg, ${colors.bg} 0%, #151b23 100%)`
          : undefined,
        boxShadow: isSelected ? colors.glow : undefined,
      }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Active indicator */}
      {isActive && (
        <motion.div
          className="absolute -top-2 -right-2 px-2 py-0.5 rounded-full text-[9px] font-mono font-medium uppercase tracking-wider"
          style={{ 
            backgroundColor: colors.bg,
            color: colors.accent,
            border: `1px solid ${colors.border}`,
          }}
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
        >
          Active
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div
          className="p-2.5 rounded-lg"
          style={{ 
            backgroundColor: isSelected ? colors.bg : "rgba(148, 163, 184, 0.06)",
            color: isSelected ? colors.accent : "#64748b",
          }}
        >
          {scenario.icon}
        </div>

        {isSelected && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: colors.accent }}
          />
        )}
      </div>

      {/* Title & Description */}
      <h3
        className="text-[15px] font-semibold mb-1"
        style={{ 
          fontFamily: "'Space Grotesk', sans-serif",
          color: isSelected ? colors.accent : "#f0f4f8",
        }}
      >
        {scenario.name}
      </h3>
      <p className="text-[12px] text-[#64748b] leading-relaxed mb-4 line-clamp-2">
        {scenario.description}
      </p>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        {[
          { label: "Risk", value: scenario.stats.avgRiskScore, color: colors.accent },
          { label: "Detection", value: scenario.stats.detectionRate, color: "#34d399" },
          { label: "Avg Amt", value: scenario.stats.avgAmount, color: "#f0f4f8" },
        ].map((stat) => (
          <div key={stat.label} className="bg-[#0f1419] rounded-lg p-2 border border-[rgba(148,163,184,0.04)]">
            <div className="text-[8px] font-mono uppercase tracking-wider text-[#64748b]">
              {stat.label}
            </div>
            <div className="text-[11px] font-mono font-semibold" style={{ color: stat.color }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Indicators */}
      <div className="space-y-1.5">
        <div className="text-[9px] font-mono uppercase tracking-wider text-[#475569] mb-2">
          Indicators
        </div>
        {scenario.indicators.slice(0, 3).map((indicator, i) => (
          <div
            key={i}
            className="flex items-center gap-2 text-[11px] text-[#94a3b8]"
          >
            <span 
              className="w-1 h-1 rounded-full"
              style={{ backgroundColor: colors.accent }}
            />
            {indicator}
          </div>
        ))}
      </div>
    </motion.button>
  );
}

// ============================================================================
// ATTACK SCENARIO GRID
// ============================================================================

interface AttackScenarioGridProps {
  selectedScenario: AttackScenario;
  activeScenario: string | null;
  onSelectScenario: (scenario: AttackScenario) => void;
  className?: string;
}

export function AttackScenarioGrid({
  selectedScenario,
  activeScenario,
  onSelectScenario,
  className,
}: AttackScenarioGridProps) {
  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4", className)}>
      {attackScenarios.map((scenario) => (
        <AttackScenarioCard
          key={scenario.id}
          scenario={scenario}
          isSelected={selectedScenario === scenario.id}
          isActive={activeScenario === scenario.id}
          onSelect={() => onSelectScenario(scenario.id)}
        />
      ))}
    </div>
  );
}

export default AttackScenarioCard;
