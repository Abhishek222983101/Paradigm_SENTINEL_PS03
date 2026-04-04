import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with clsx
 * Handles conditional classes and deduplication
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency with proper symbol
 */
export function formatCurrency(amount: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format timestamp to human-readable
 */
export function formatTimestamp(timestamp: string | Date): string {
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

/**
 * Format full date
 */
export function formatDate(timestamp: string | Date): string {
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}

/**
 * Get risk level from score
 */
export function getRiskLevel(score: number): "safe" | "warning" | "critical" {
  if (score < 40) return "safe";
  if (score < 70) return "warning";
  return "critical";
}

/**
 * Get action color based on decision
 */
export function getActionColor(action: string): string {
  switch (action.toUpperCase()) {
    case "ALLOW":
      return "terminal-green";
    case "BLOCK":
      return "neon-crimson";
    case "MFA":
    case "CHALLENGE":
      return "warning-amber";
    default:
      return "cyber-cyan";
  }
}

/**
 * Generate random transaction ID
 */
export function generateTxnId(): string {
  const date = new Date().toISOString().split("T")[0];
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `TXN-${date}-${random}`;
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

/**
 * Delay utility for animations
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Format milliseconds to readable latency
 */
export function formatLatency(ms: number): string {
  if (ms < 1) return "<1ms";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Format large numbers with K/M/B suffix
 */
export function formatNumber(num: number): string {
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

/**
 * Format amount with commas (consistent across server/client)
 * Uses en-US locale explicitly to avoid hydration mismatch
 */
export function formatAmount(amount: number, decimals: number = 0): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount);
}

/**
 * Generate stagger delay for animations
 */
export function staggerDelay(index: number, baseDelay: number = 0.05): number {
  return index * baseDelay;
}
