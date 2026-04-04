// ═══════════════════════════════════════════════════════════════════════════
// SENTINEL SIMULATOR CONTROLS
// Attack Injection Control Panel - Refined Design
// ═══════════════════════════════════════════════════════════════════════════

"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AttackScenario } from "@/types";
import {
  Play,
  Square,
  Zap,
  Clock,
  Gauge,
  AlertTriangle,
  RefreshCw,
  BarChart3,
  Target,
} from "lucide-react";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

export type AttackIntensity = "low" | "medium" | "high";

interface SimulatorControlsProps {
  selectedScenario: AttackScenario;
  isRunning: boolean;
  onStart: (config: {
    scenario: AttackScenario;
    intensity: AttackIntensity;
    duration: number;
    transactionsPerSecond: number;
  }) => void;
  onStop: () => void;
  onReset: () => void;
  className?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTENSITY SELECTOR
// ═══════════════════════════════════════════════════════════════════════════

interface IntensitySelectorProps {
  value: AttackIntensity;
  onChange: (value: AttackIntensity) => void;
}

function IntensitySelector({ value, onChange }: IntensitySelectorProps) {
  const intensities: { id: AttackIntensity; label: string; tps: string; color: string }[] = [
    { id: "low", label: "Low", color: "success", tps: "1-2 TPS" },
    { id: "medium", label: "Medium", color: "warning", tps: "5-10 TPS" },
    { id: "high", label: "High", color: "danger", tps: "20-50 TPS" },
  ];

  const getColors = (id: AttackIntensity, isSelected: boolean) => {
    const colorMap = {
      low: {
        border: isSelected ? "border-[var(--accent-success)]" : "border-[var(--border-default)]",
        bg: isSelected ? "bg-[var(--accent-success-glow)]" : "bg-transparent",
        text: isSelected ? "text-[var(--accent-success)]" : "text-[var(--text-muted)]",
      },
      medium: {
        border: isSelected ? "border-[var(--accent-warning)]" : "border-[var(--border-default)]",
        bg: isSelected ? "bg-[var(--accent-warning-glow)]" : "bg-transparent",
        text: isSelected ? "text-[var(--accent-warning)]" : "text-[var(--text-muted)]",
      },
      high: {
        border: isSelected ? "border-[var(--accent-danger)]" : "border-[var(--border-default)]",
        bg: isSelected ? "bg-[var(--accent-danger-glow)]" : "bg-transparent",
        text: isSelected ? "text-[var(--accent-danger)]" : "text-[var(--text-muted)]",
      },
    };
    return colorMap[id];
  };

  return (
    <div className="space-y-2">
      <label className="data-label flex items-center gap-2">
        <Gauge className="w-3 h-3" />
        Attack Intensity
      </label>
      <div className="flex gap-2">
        {intensities.map((intensity) => {
          const colors = getColors(intensity.id, value === intensity.id);
          return (
            <button
              key={intensity.id}
              onClick={() => onChange(intensity.id)}
              className={cn(
                "flex-1 py-3 px-3 rounded-lg border font-medium text-sm transition-all",
                colors.border,
                colors.bg,
                colors.text,
                "hover:border-[var(--border-strong)]"
              )}
            >
              <div className="font-semibold">{intensity.label}</div>
              <div className="text-[10px] mt-0.5 opacity-70">{intensity.tps}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// DURATION SLIDER
// ═══════════════════════════════════════════════════════════════════════════

interface DurationSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
}

function DurationSlider({ value, onChange, min = 5, max = 60 }: DurationSliderProps) {
  return (
    <div className="space-y-2">
      <label className="data-label flex items-center justify-between">
        <span className="flex items-center gap-2">
          <Clock className="w-3 h-3" />
          Duration
        </span>
        <span className="text-[var(--accent-primary)] font-semibold">{value}s</span>
      </label>
      <div className="relative pt-1">
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="w-full h-2 bg-[var(--bg-muted)] rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4
            [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:bg-[var(--accent-primary)]
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:cursor-pointer
            [&::-webkit-slider-thumb]:transition-all
            [&::-webkit-slider-thumb]:hover:scale-110
            [&::-webkit-slider-thumb]:shadow-[0_0_10px_var(--accent-primary-glow)]
          "
        />
        <div className="flex justify-between text-[10px] text-[var(--text-dim)] font-mono mt-2">
          <span>{min}s</span>
          <span>{max}s</span>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// TPS CONTROL
// ═══════════════════════════════════════════════════════════════════════════

interface TPSControlProps {
  value: number;
  onChange: (value: number) => void;
  intensity: AttackIntensity;
}

function TPSControl({ value, onChange, intensity }: TPSControlProps) {
  const presets: Record<AttackIntensity, number[]> = {
    low: [1, 2, 3, 5],
    medium: [5, 10, 15, 20],
    high: [20, 30, 40, 50],
  };

  return (
    <div className="space-y-2">
      <label className="data-label flex items-center justify-between">
        <span className="flex items-center gap-2">
          <BarChart3 className="w-3 h-3" />
          Transactions/Second
        </span>
        <span className="text-[var(--accent-primary)] font-semibold">{value} TPS</span>
      </label>
      <div className="flex gap-2">
        {presets[intensity].map((preset) => (
          <button
            key={preset}
            onClick={() => onChange(preset)}
            className={cn(
              "flex-1 py-2 rounded-md border font-mono text-sm transition-all",
              value === preset
                ? "border-[var(--accent-primary)] bg-[var(--accent-primary-glow)] text-[var(--accent-primary)]"
                : "border-[var(--border-default)] text-[var(--text-muted)] hover:border-[var(--border-strong)]"
            )}
          >
            {preset}
          </button>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// LIVE STATS - With proper state management (no Math.random in render)
// ═══════════════════════════════════════════════════════════════════════════

interface LiveStatsProps {
  isRunning: boolean;
  tps: number;
}

function LiveStats({ isRunning, tps }: LiveStatsProps) {
  const [stats, setStats] = useState({
    txnInjected: 0,
    fraudDetected: 0,
    alertsTriggered: 0,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isRunning) {
      // Initialize with some values
      setStats({
        txnInjected: 10 + Math.floor(Math.random() * 20),
        fraudDetected: 2 + Math.floor(Math.random() * 5),
        alertsTriggered: 1 + Math.floor(Math.random() * 3),
      });

      // Update periodically
      intervalRef.current = setInterval(() => {
        setStats(prev => ({
          txnInjected: prev.txnInjected + Math.floor(Math.random() * 5) + 1,
          fraudDetected: prev.fraudDetected + (Math.random() > 0.7 ? 1 : 0),
          alertsTriggered: prev.alertsTriggered + (Math.random() > 0.8 ? 1 : 0),
        }));
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setStats({ txnInjected: 0, fraudDetected: 0, alertsTriggered: 0 });
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning]);

  if (!isRunning) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-4 gap-4 pt-4 border-t border-[var(--border-default)]"
    >
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-[var(--accent-primary)]">
          {stats.txnInjected}
        </div>
        <div className="text-[10px] text-[var(--text-muted)] font-mono uppercase">
          TXNs Injected
        </div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-[var(--accent-danger)]">
          {stats.fraudDetected}
        </div>
        <div className="text-[10px] text-[var(--text-muted)] font-mono uppercase">
          Fraud Detected
        </div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-[var(--accent-warning)]">
          {stats.alertsTriggered}
        </div>
        <div className="text-[10px] text-[var(--text-muted)] font-mono uppercase">
          Alerts Triggered
        </div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-[var(--accent-success)]">
          {tps}
        </div>
        <div className="text-[10px] text-[var(--text-muted)] font-mono uppercase">
          Current TPS
        </div>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function SimulatorControls({
  selectedScenario,
  isRunning,
  onStart,
  onStop,
  onReset,
  className,
}: SimulatorControlsProps) {
  const [intensity, setIntensity] = useState<AttackIntensity>("medium");
  const [duration, setDuration] = useState(15);
  const [tps, setTps] = useState(10);

  const handleStart = () => {
    onStart({
      scenario: selectedScenario,
      intensity,
      duration,
      transactionsPerSecond: tps,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "panel space-y-5",
        isRunning && "border-[var(--accent-danger)] shadow-[0_0_30px_var(--accent-danger-glow)]",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "p-2.5 rounded-lg",
              isRunning
                ? "bg-[var(--accent-danger-glow)]"
                : "bg-[var(--accent-primary-glow)]"
            )}
          >
            <Target
              className={cn(
                "w-5 h-5",
                isRunning ? "text-[var(--accent-danger)]" : "text-[var(--accent-primary)]"
              )}
            />
          </div>
          <div>
            <h2 className="font-heading text-base font-semibold text-[var(--text-primary)]">
              Injection Controls
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              Configure and launch attack simulation
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div
          className={cn(
            "status-badge",
            isRunning ? "bg-[var(--accent-danger-glow)] text-[var(--accent-danger)] border border-[var(--accent-danger)]/30" 
                      : "live"
          )}
        >
          {isRunning ? (
            <>
              <motion.span
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="status-dot bg-[var(--accent-danger)]"
              />
              Attack Running
            </>
          ) : (
            <>
              <span className="status-dot live" />
              Ready
            </>
          )}
        </div>
      </div>

      {/* Selected Scenario Display */}
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-lg p-4">
        <div className="data-label mb-2">
          Selected Scenario
        </div>
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "text-xl font-heading font-semibold capitalize",
              selectedScenario === "normal"
                ? "text-[var(--accent-success)]"
                : selectedScenario === "account_takeover" ||
                  selectedScenario === "fraud_ring"
                ? "text-[var(--accent-danger)]"
                : "text-[var(--accent-warning)]"
            )}
          >
            {selectedScenario.replace("_", " ")}
          </div>
        </div>
      </div>

      {/* Controls Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <IntensitySelector value={intensity} onChange={setIntensity} />
        <DurationSlider value={duration} onChange={setDuration} />
        <TPSControl value={tps} onChange={setTps} intensity={intensity} />
      </div>

      {/* Warning Banner */}
      {selectedScenario !== "normal" && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="alert-banner"
        >
          <AlertTriangle className="w-5 h-5 text-[var(--accent-warning)] flex-shrink-0" />
          <p className="alert-banner-text text-sm">
            This will inject {selectedScenario.replace("_", " ")} attack transactions into the stream. 
            All transactions will be logged and flagged as simulated.
          </p>
        </motion.div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        {!isRunning ? (
          <motion.button
            onClick={handleStart}
            className={cn(
              "flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold text-sm transition-all",
              selectedScenario === "normal"
                ? "bg-[var(--accent-success)] text-[var(--bg-base)] hover:shadow-[0_0_20px_var(--accent-success-glow)]"
                : "bg-[var(--accent-danger)] text-white hover:shadow-[0_0_20px_var(--accent-danger-glow)]"
            )}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <Zap className="w-4 h-4" />
            {selectedScenario === "normal" ? "Start Stream" : "Launch Attack"}
          </motion.button>
        ) : (
          <motion.button
            onClick={onStop}
            className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold text-sm bg-[var(--text-primary)] text-[var(--bg-base)] hover:opacity-90 transition-all"
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <Square className="w-4 h-4" />
            Stop Attack
          </motion.button>
        )}

        <motion.button
          onClick={onReset}
          className="px-4 py-3 rounded-lg border border-[var(--border-default)] text-[var(--text-muted)] hover:border-[var(--border-strong)] hover:text-[var(--text-primary)] transition-all"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          title="Reset"
        >
          <RefreshCw className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Live Stats During Attack */}
      <LiveStats isRunning={isRunning} tps={tps} />
    </motion.div>
  );
}

export default SimulatorControls;
