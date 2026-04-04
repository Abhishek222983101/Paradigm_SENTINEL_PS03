// ============================================================================
// SENTINEL GLOBAL LOADING STATE
// Shown during route transitions
// ============================================================================

import { Shield } from "lucide-react";

export default function Loading() {
  return (
    <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
      <div className="text-center">
        {/* Animated Shield */}
        <div className="relative mx-auto w-16 h-16 mb-6">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border-2 border-[rgba(56,189,248,0.2)]" />
          
          {/* Spinning ring */}
          <div 
            className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#38bdf8] animate-spin"
          />
          
          {/* Center icon */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Shield className="w-6 h-6 text-[#38bdf8]" />
          </div>
        </div>

        {/* Loading text */}
        <div className="text-sm font-mono text-[#64748b] uppercase tracking-wider">
          Loading<span className="animate-pulse">...</span>
        </div>

        {/* Pulse bar */}
        <div className="mt-6 w-48 h-1 bg-[#151b23] rounded-full overflow-hidden mx-auto">
          <div 
            className="h-full w-1/2 bg-gradient-to-r from-transparent via-[#38bdf8] to-transparent animate-pulse"
          />
        </div>
      </div>
    </div>
  );
}
