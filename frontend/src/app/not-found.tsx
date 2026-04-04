// ============================================================================
// SENTINEL 404 NOT FOUND PAGE
// Custom 404 error page
// ============================================================================

"use client";

import { motion } from "framer-motion";
import { Shield, Home, Search, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full text-center"
      >
        {/* 404 Display */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200, damping: 15 }}
          className="mb-8"
        >
          <div className="text-8xl font-mono font-bold text-[#151b23] relative">
            404
            <div className="absolute inset-0 text-8xl font-mono font-bold bg-gradient-to-r from-[#38bdf8] to-[#a78bfa] bg-clip-text text-transparent opacity-50 blur-sm">
              404
            </div>
          </div>
        </motion.div>

        {/* Message */}
        <h1 className="text-2xl font-semibold text-[#f0f4f8] mb-3">
          Page Not Found
        </h1>
        <p className="text-[#64748b] text-sm mb-8 leading-relaxed">
          The page you're looking for doesn't exist or has been moved.
          Our fraud detection system is still operational.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.3)] text-[#38bdf8] font-medium text-sm hover:bg-[rgba(56,189,248,0.15)] transition-all"
          >
            <Home className="w-4 h-4" />
            Go Home
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#94a3b8] font-medium text-sm hover:text-[#f0f4f8] hover:border-[rgba(148,163,184,0.2)] transition-all"
          >
            <Search className="w-4 h-4" />
            Dashboard
          </Link>
        </div>

        {/* Quick Links */}
        <div className="mt-12 pt-8 border-t border-[rgba(148,163,184,0.08)]">
          <div className="text-[10px] font-mono uppercase text-[#64748b] mb-4">
            Quick Links
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              { label: "Dashboard", href: "/dashboard" },
              { label: "Simulator", href: "/simulator" },
              { label: "Investigation", href: "/investigation" },
              { label: "Graph", href: "/graph" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-1.5 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.08)] text-xs text-[#94a3b8] hover:text-[#38bdf8] hover:border-[rgba(56,189,248,0.3)] transition-all"
              >
                {link.label}
              </Link>
            ))}
          </div>
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
