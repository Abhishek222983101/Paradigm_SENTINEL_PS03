// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL RISK GAUGE COMPONENT
// Animated Risk Score Meter - Refined Design
// ═══════════════════════════════════════════════════════════════════════════

"use client";

import { useEffect, useState, useRef } from "react";
import { motion, useSpring, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface RiskGaugeProps {
  value: number;
  max?: number;
  size?: "sm" | "md" | "lg" | "xl";
  label?: string;
  showValue?: boolean;
  className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// SIZE CONFIGURATIONS
// ═══════════════════════════════════════════════════════════════════════════

const sizeConfig = {
  sm: { radius: 50, strokeWidth: 8, fontSize: "text-xl", labelSize: "text-xs" },
  md: { radius: 70, strokeWidth: 10, fontSize: "text-3xl", labelSize: "text-sm" },
  lg: { radius: 90, strokeWidth: 12, fontSize: "text-4xl", labelSize: "text-base" },
  xl: { radius: 120, strokeWidth: 16, fontSize: "text-5xl", labelSize: "text-lg" },
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function getRiskColor(value: number): { color: string; glow: string; bg: string } {
  if (value >= 85) {
    return {
      color: "var(--accent-danger)",
      glow: "0 0 20px var(--accent-danger-glow)",
      bg: "var(--accent-danger-glow)",
    };
  }
  if (value >= 70) {
    return {
      color: "var(--accent-warning)",
      glow: "0 0 18px var(--accent-warning-glow)",
      bg: "var(--accent-warning-glow)",
    };
  }
  if (value >= 40) {
    return {
      color: "var(--accent-primary)",
      glow: "0 0 15px var(--accent-primary-glow)",
      bg: "var(--accent-primary-glow)",
    };
  }
  return {
    color: "var(--accent-success)",
    glow: "0 0 12px var(--accent-success-glow)",
    bg: "var(--accent-success-glow)",
  };
}

function getRiskLabel(value: number): string {
  if (value >= 85) return "CRITICAL";
  if (value >= 70) return "HIGH";
  if (value >= 40) return "MEDIUM";
  return "LOW";
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function RiskGauge({
  value,
  max = 100,
  size = "md",
  label,
  showValue = true,
  className,
}: RiskGaugeProps) {
  const config = sizeConfig[size];
  const { radius, strokeWidth, fontSize, labelSize } = config;

  // Calculate dimensions
  const svgSize = (radius + strokeWidth) * 2;
  const halfCircumference = Math.PI * radius;

  // Animated value using spring
  const springValue = useSpring(0, { stiffness: 100, damping: 20 });
  const displayValue = useTransform(springValue, (v) => Math.round(v));
  const strokeDashoffset = useTransform(
    springValue,
    (v) => halfCircumference - (v / max) * halfCircumference
  );

  // Update spring when value changes
  useEffect(() => {
    springValue.set(value);
  }, [value, springValue]);

  // Get colors based on current value
  const { color, glow, bg } = getRiskColor(value);
  const riskLabel = getRiskLabel(value);

  // Track previous value for flash effect
  const [isFlashing, setIsFlashing] = useState(false);
  const prevValueRef = useRef(value);

  useEffect(() => {
    if (Math.abs(value - prevValueRef.current) > 10) {
      setIsFlashing(true);
      setTimeout(() => setIsFlashing(false), 300);
    }
    prevValueRef.current = value;
  }, [value]);

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center",
        "p-5 rounded-xl border border-[var(--border-default)]",
        "bg-[var(--bg-elevated)]",
        isFlashing && "ring-2 ring-offset-2 ring-offset-[var(--bg-base)]",
        value >= 85 && isFlashing && "ring-[var(--accent-danger)]",
        value >= 70 && value < 85 && isFlashing && "ring-[var(--accent-warning)]",
        className
      )}
    >
      {/* SVG Gauge */}
      <div className="relative" style={{ width: svgSize, height: svgSize / 2 + strokeWidth }}>
        <svg
          width={svgSize}
          height={svgSize / 2 + strokeWidth}
          viewBox={`0 0 ${svgSize} ${svgSize / 2 + strokeWidth}`}
          className="overflow-visible"
        >
          {/* Background arc */}
          <path
            d={`
              M ${strokeWidth} ${radius + strokeWidth}
              A ${radius} ${radius} 0 0 1 ${svgSize - strokeWidth} ${radius + strokeWidth}
            `}
            fill="none"
            stroke="var(--bg-muted)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = Math.PI - (tick / 100) * Math.PI;
            const x1 = radius + strokeWidth + (radius - strokeWidth - 5) * Math.cos(angle);
            const y1 = radius + strokeWidth - (radius - strokeWidth - 5) * Math.sin(angle);
            const x2 = radius + strokeWidth + (radius + 5) * Math.cos(angle);
            const y2 = radius + strokeWidth - (radius + 5) * Math.sin(angle);

            return (
              <line
                key={tick}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="var(--text-dim)"
                strokeWidth={2}
              />
            );
          })}

          {/* Animated progress arc */}
          <motion.path
            d={`
              M ${strokeWidth} ${radius + strokeWidth}
              A ${radius} ${radius} 0 0 1 ${svgSize - strokeWidth} ${radius + strokeWidth}
            `}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={halfCircumference}
            style={{
              strokeDashoffset,
              filter: `drop-shadow(${glow})`,
            }}
          />

          {/* Needle indicator */}
          <motion.g
            style={{
              transformOrigin: `${radius + strokeWidth}px ${radius + strokeWidth}px`,
            }}
            animate={{
              rotate: -90 + (value / max) * 180,
            }}
            transition={{ type: "spring", stiffness: 100, damping: 20 }}
          >
            <line
              x1={radius + strokeWidth}
              y1={radius + strokeWidth}
              x2={radius + strokeWidth}
              y2={strokeWidth + 15}
              stroke={color}
              strokeWidth={3}
              strokeLinecap="round"
              style={{ filter: `drop-shadow(${glow})` }}
            />
            <circle
              cx={radius + strokeWidth}
              cy={radius + strokeWidth}
              r={8}
              fill="var(--bg-base)"
              stroke={color}
              strokeWidth={2}
            />
          </motion.g>
        </svg>

        {/* Center value display */}
        {showValue && (
          <div
            className="absolute left-1/2 -translate-x-1/2"
            style={{ bottom: 0 }}
          >
            <motion.div
              className={cn(
                "font-mono font-bold tabular-nums",
                fontSize
              )}
              style={{ color }}
            >
              {displayValue}
            </motion.div>
          </div>
        )}
      </div>

      {/* Risk Level Label */}
      <motion.div
        className={cn(
          "mt-3 px-3 py-1 rounded-full font-mono font-semibold uppercase tracking-wider text-xs",
          "border"
        )}
        style={{
          backgroundColor: bg,
          color: color,
          borderColor: `color-mix(in srgb, ${color} 30%, transparent)`,
        }}
        animate={
          value >= 85
            ? { opacity: [1, 0.6, 1] }
            : { opacity: 1 }
        }
        transition={
          value >= 85
            ? { duration: 0.8, repeat: Infinity }
            : {}
        }
      >
        {riskLabel}
      </motion.div>

      {/* Custom label */}
      {label && (
        <div className={cn("mt-2 text-[var(--text-muted)] font-mono uppercase tracking-wider", labelSize)}>
          {label}
        </div>
      )}

      {/* Danger zone indicator */}
      {value >= 85 && (
        <motion.div
          className="absolute inset-0 border-2 border-[var(--accent-danger)]/40 rounded-xl pointer-events-none"
          animate={{ opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MINI GAUGE FOR COMPACT DISPLAYS
// ═══════════════════════════════════════════════════════════════════════════

interface MiniGaugeProps {
  value: number;
  size?: number;
  className?: string;
}

export function MiniGauge({ value, size = 40, className }: MiniGaugeProps) {
  const { color } = getRiskColor(value);
  const radius = size / 2 - 4;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--bg-muted)"
          strokeWidth={3}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </svg>
      <span
        className="absolute text-xs font-mono font-semibold"
        style={{ color }}
      >
        {value}
      </span>
    </div>
  );
}

export default RiskGauge;
