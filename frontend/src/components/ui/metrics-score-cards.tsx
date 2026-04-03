"use client";

import { motion, useInView, useSpring, useTransform } from "framer-motion";
import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: number;
  maxValue?: number;
  unit?: string;
  color?: "cyan" | "crimson" | "amber" | "green";
  description?: string;
  index?: number;
}

/**
 * SENTINEL Metric Card
 * Half-circle gauge with brutal styling
 * Animated value counter with spring physics
 */
export function MetricCard({
  label,
  value,
  maxValue = 100,
  unit = "%",
  color = "cyan",
  description,
  index = 0,
}: MetricCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const [hasAnimated, setHasAnimated] = useState(false);

  const colorMap = {
    cyan: {
      stroke: "#00E5FF",
      bg: "bg-cyber-cyan",
      text: "text-cyber-cyan",
      glow: "shadow-[0_0_30px_rgba(0,229,255,0.3)]",
    },
    crimson: {
      stroke: "#FF003C",
      bg: "bg-neon-crimson",
      text: "text-neon-crimson",
      glow: "shadow-[0_0_30px_rgba(255,0,60,0.3)]",
    },
    amber: {
      stroke: "#FFB800",
      bg: "bg-warning-amber",
      text: "text-warning-amber",
      glow: "shadow-[0_0_30px_rgba(255,184,0,0.3)]",
    },
    green: {
      stroke: "#39FF14",
      bg: "bg-terminal-green",
      text: "text-terminal-green",
      glow: "shadow-[0_0_30px_rgba(57,255,20,0.3)]",
    },
  };

  const colors = colorMap[color];
  const percentage = (value / maxValue) * 100;
  const circumference = 251.2; // Half circle circumference for r=80
  const strokeOffset = circumference - (circumference * Math.min(percentage, 100)) / 100;

  // Animated counter
  const spring = useSpring(0, { stiffness: 100, damping: 30 });
  const displayValue = useTransform(spring, (v) => Math.round(v));

  useEffect(() => {
    if (isInView && !hasAnimated) {
      spring.set(value);
      setHasAnimated(true);
    }
  }, [isInView, value, spring, hasAnimated]);

  return (
    <motion.div
      ref={ref}
      className={cn(
        "relative bg-carbon border-4 border-white p-6",
        "shadow-[4px_4px_0px_#fff]",
        "hover:shadow-[8px_8px_0px_#fff] hover:translate-x-[-2px] hover:translate-y-[-2px]",
        "transition-all duration-150"
      )}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
      transition={{
        delay: index * 0.1,
        duration: 0.4,
        type: "spring",
        stiffness: 400,
        damping: 25,
      }}
    >
      {/* Label */}
      <div className="text-sm font-mono text-steel uppercase tracking-wider mb-4">
        {label}
      </div>

      {/* Half-circle gauge */}
      <div className="relative w-full aspect-[2/1] mb-4">
        <svg
          viewBox="0 0 200 110"
          className="w-full h-full"
          style={{ transform: "rotate(0deg)" }}
        >
          {/* Background arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="#252525"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Animated arc */}
          <motion.path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={colors.stroke}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={
              isInView
                ? { strokeDashoffset: strokeOffset }
                : { strokeDashoffset: circumference }
            }
            transition={{
              delay: index * 0.1 + 0.3,
              duration: 1.2,
              ease: [0.16, 1, 0.3, 1],
            }}
            style={{
              filter: `drop-shadow(0 0 10px ${colors.stroke})`,
            }}
          />

          {/* Center tick marks */}
          {[0, 25, 50, 75, 100].map((tick, i) => {
            const angle = (tick / 100) * 180 - 180;
            const radian = (angle * Math.PI) / 180;
            const x1 = 100 + 65 * Math.cos(radian);
            const y1 = 100 + 65 * Math.sin(radian);
            const x2 = 100 + 75 * Math.cos(radian);
            const y2 = 100 + 75 * Math.sin(radian);

            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#8B8B8B"
                strokeWidth="2"
              />
            );
          })}
        </svg>

        {/* Value display */}
        <div className="absolute inset-0 flex items-end justify-center pb-2">
          <motion.span
            className={cn(
              "text-4xl md:text-5xl font-heading font-bold",
              colors.text
            )}
            style={{
              textShadow: `0 0 20px ${colors.stroke}`,
            }}
          >
            <motion.span>{displayValue}</motion.span>
            <span className="text-xl ml-1">{unit}</span>
          </motion.span>
        </div>
      </div>

      {/* Description */}
      {description && (
        <div className="text-xs font-mono text-steel text-center">
          {description}
        </div>
      )}

      {/* Status indicator */}
      <motion.div
        className={cn(
          "absolute top-4 right-4 w-3 h-3 rounded-full",
          colors.bg
        )}
        animate={{
          opacity: [1, 0.5, 1],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        style={{
          boxShadow: `0 0 10px ${colors.stroke}`,
        }}
      />
    </motion.div>
  );
}

interface MetricsGridProps {
  metrics: Array<{
    label: string;
    value: number;
    maxValue?: number;
    unit?: string;
    color?: "cyan" | "crimson" | "amber" | "green";
    description?: string;
  }>;
  className?: string;
}

/**
 * SENTINEL Metrics Grid
 * Grid of fraud detection metrics with staggered animation
 */
export function MetricsGrid({ metrics, className }: MetricsGridProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
        className
      )}
    >
      {metrics.map((metric, index) => (
        <MetricCard key={metric.label} {...metric} index={index} />
      ))}
    </div>
  );
}

// Default fraud detection metrics
export const defaultFraudMetrics = [
  {
    label: "Detection Rate",
    value: 97.3,
    maxValue: 100,
    unit: "%",
    color: "cyan" as const,
    description: "ML model accuracy",
  },
  {
    label: "Avg Latency",
    value: 42,
    maxValue: 100,
    unit: "ms",
    color: "green" as const,
    description: "End-to-end processing",
  },
  {
    label: "False Positives",
    value: 2.1,
    maxValue: 10,
    unit: "%",
    color: "amber" as const,
    description: "Incorrectly flagged",
  },
  {
    label: "Fraud Blocked",
    value: 847,
    maxValue: 1000,
    unit: "K",
    color: "crimson" as const,
    description: "Last 24 hours",
  },
];

export default MetricsGrid;
