// ============================================================================
// SENTINEL ERROR BOUNDARY
// Global error handler for the application
// ============================================================================

"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, RefreshCw, Home, Shield } from "lucide-react";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log the error to console (could be sent to error tracking service)
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full text-center"
      >
        {/* Error Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 15 }}
          className="mx-auto w-20 h-20 rounded-2xl bg-[rgba(248,113,113,0.1)] border border-[rgba(248,113,113,0.3)] flex items-center justify-center mb-6"
        >
          <AlertTriangle className="w-10 h-10 text-[#f87171]" />
        </motion.div>

        {/* Error Message */}
        <h1 className="text-2xl font-semibold text-[#f0f4f8] mb-3">
          Something went wrong
        </h1>
        <p className="text-[#64748b] text-sm mb-6 leading-relaxed">
          The SENTINEL system encountered an unexpected error. 
          Our fraud detection algorithms are still running - this is just a display issue.
        </p>

        {/* Error Details (development only) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mb-6 p-4 bg-[#151b23] rounded-lg border border-[rgba(148,163,184,0.08)] text-left">
            <div className="text-[10px] font-mono uppercase text-[#64748b] mb-2">
              Error Details
            </div>
            <code className="text-xs text-[#f87171] font-mono break-all">
              {error.message}
            </code>
            {error.digest && (
              <div className="mt-2 text-[10px] text-[#64748b] font-mono">
                Digest: {error.digest}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.3)] text-[#38bdf8] font-medium text-sm hover:bg-[rgba(56,189,248,0.15)] transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
          <Link
            href="/"
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#94a3b8] font-medium text-sm hover:text-[#f0f4f8] hover:border-[rgba(148,163,184,0.2)] transition-all"
          >
            <Home className="w-4 h-4" />
            Go Home
          </Link>
        </div>

        {/* SENTINEL Footer */}
        <div className="mt-12 flex items-center justify-center gap-2 text-[#4b5563]">
          <Shield className="w-4 h-4" />
          <span className="text-xs font-mono">SENTINEL v1.0</span>
        </div>
      </motion.div>
    </div>
  );
}
