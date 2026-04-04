// ============================================================================
// SENTINEL SHAP WATERFALL CHART
// Visual explanation of ML model decision factors
// ============================================================================

"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Info } from "lucide-react";

interface SHAPValue {
  feature: string;
  value: number;
  description?: string;
}

interface SHAPChartProps {
  shapValues: Record<string, number>;
  baseScore?: number;
  className?: string;
}

const featureLabels: Record<string, { label: string; description: string }> = {
  amount: { label: "Transaction Amount", description: "Unusually high or pattern-breaking amount" },
  location: { label: "Location Risk", description: "Geographic anomaly or high-risk region" },
  device: { label: "Device Trust", description: "New or suspicious device fingerprint" },
  velocity: { label: "Transaction Velocity", description: "Rapid succession of transactions" },
  merchant: { label: "Merchant Category", description: "High-risk merchant type" },
  time_of_day: { label: "Time Pattern", description: "Unusual transaction timing" },
  user_history: { label: "User Behavior", description: "Deviation from normal patterns" },
  ip_risk: { label: "IP Risk Score", description: "VPN, proxy, or blacklisted IP" },
  card_presence: { label: "Card Not Present", description: "CNP transaction risk" },
  cross_border: { label: "Cross-Border", description: "International transaction flag" },
};

export function SHAPChart({ shapValues, baseScore = 50, className }: SHAPChartProps) {
  const sortedValues = useMemo(() => {
    return Object.entries(shapValues)
      .map(([feature, value]) => ({
        feature,
        value,
        info: featureLabels[feature] || { label: feature, description: "" },
      }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  }, [shapValues]);

  const maxAbsValue = Math.max(...sortedValues.map((v) => Math.abs(v.value)), 0.5);
  const finalScore = baseScore + sortedValues.reduce((acc, v) => acc + v.value * 100, 0);

  return (
    <div className={cn("bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-xl overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-[#38bdf8]" />
          <h3
            className="text-[14px] font-semibold text-[#f0f4f8]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Risk Factor Analysis (SHAP)
          </h3>
        </div>
        <div className="text-xs font-mono text-[#64748b]">
          Base: {baseScore}% → Final: {finalScore.toFixed(0)}%
        </div>
      </div>

      {/* Chart */}
      <div className="p-5 space-y-3">
        {sortedValues.map((item, index) => {
          const isPositive = item.value > 0;
          const barWidth = (Math.abs(item.value) / maxAbsValue) * 100;
          const contribution = (item.value * 100).toFixed(1);

          return (
            <motion.div
              key={item.feature}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="group"
            >
              <div className="flex items-center gap-4">
                {/* Feature Label */}
                <div className="w-40 flex-shrink-0">
                  <div className="text-[13px] text-[#f0f4f8] font-medium truncate">
                    {item.info.label}
                  </div>
                  <div className="text-[10px] text-[#64748b] truncate opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.info.description}
                  </div>
                </div>

                {/* Bar Chart */}
                <div className="flex-1 flex items-center gap-2">
                  {/* Negative side */}
                  <div className="flex-1 flex justify-end">
                    {!isPositive && (
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${barWidth}%` }}
                        transition={{ delay: index * 0.05 + 0.2, duration: 0.4 }}
                        className="h-6 rounded-l-md bg-gradient-to-r from-[#34d399] to-[#34d399]/70 flex items-center justify-start px-2"
                      >
                        <TrendingDown className="w-3 h-3 text-[#0a0e14]" />
                      </motion.div>
                    )}
                  </div>

                  {/* Center line */}
                  <div className="w-px h-8 bg-[#64748b]/30 flex-shrink-0" />

                  {/* Positive side */}
                  <div className="flex-1 flex justify-start">
                    {isPositive && (
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${barWidth}%` }}
                        transition={{ delay: index * 0.05 + 0.2, duration: 0.4 }}
                        className="h-6 rounded-r-md bg-gradient-to-r from-[#f87171]/70 to-[#f87171] flex items-center justify-end px-2"
                      >
                        <TrendingUp className="w-3 h-3 text-[#0a0e14]" />
                      </motion.div>
                    )}
                  </div>
                </div>

                {/* Value */}
                <div
                  className={cn(
                    "w-16 text-right font-mono text-sm font-semibold",
                    isPositive ? "text-[#f87171]" : "text-[#34d399]"
                  )}
                >
                  {isPositive ? "+" : ""}{contribution}%
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Footer Legend */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#0f1419] border-t border-[rgba(148,163,184,0.08)]">
        <div className="flex items-center gap-4 text-[11px] font-mono">
          <span className="flex items-center gap-1.5 text-[#34d399]">
            <span className="w-3 h-3 rounded bg-[#34d399]" />
            Decreases Risk
          </span>
          <span className="flex items-center gap-1.5 text-[#f87171]">
            <span className="w-3 h-3 rounded bg-[#f87171]" />
            Increases Risk
          </span>
        </div>
        <div className="text-[10px] text-[#64748b]">
          SHAP (SHapley Additive exPlanations)
        </div>
      </div>
    </div>
  );
}

export default SHAPChart;
