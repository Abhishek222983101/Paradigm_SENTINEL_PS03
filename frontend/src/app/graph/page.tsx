// ============================================================================
// SENTINEL GRAPH VISUALIZATION PAGE
// Interactive fraud ring detection and network analysis
// ============================================================================

"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { FloatingHeader } from "@/components/layout";
import { FraudGraph, type FraudGraphRef } from "@/components/graph/FraudGraph";
import {
  Network,
  Search,
  AlertTriangle,
  Users,
  Smartphone,
  Globe,
  CreditCard,
  RefreshCw,
  Download,
  Filter,
  ChevronRight,
} from "lucide-react";
import { cn, formatAmount } from "@/lib/utils";

// ============================================================================
// TYPES
// ============================================================================

interface RingDetection {
  ring_id: string;
  members: number;
  total_fraud_amount: number;
  risk_level: "critical" | "high" | "medium";
  detected_at: string;
  status: "active" | "under_investigation" | "neutralized";
}

// ============================================================================
// MOCK DATA
// ============================================================================

const mockRingDetections: RingDetection[] = [
  {
    ring_id: "RING-001",
    members: 4,
    total_fraud_amount: 125000,
    risk_level: "critical",
    detected_at: "2026-04-04T10:30:00Z",
    status: "active",
  },
  {
    ring_id: "RING-002",
    members: 7,
    total_fraud_amount: 89500,
    risk_level: "high",
    detected_at: "2026-04-03T15:45:00Z",
    status: "under_investigation",
  },
  {
    ring_id: "RING-003",
    members: 3,
    total_fraud_amount: 45000,
    risk_level: "medium",
    detected_at: "2026-04-02T09:00:00Z",
    status: "neutralized",
  },
];

const quickSearchUsers = [
  { id: "USR-4421", name: "Primary Target", risk: 94 },
  { id: "USR-7892", name: "Connected User", risk: 72 },
  { id: "USR-1156", name: "Ring Member", risk: 91 },
  { id: "USR-3341", name: "Secondary Actor", risk: 68 },
];

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function GraphPage() {
  const graphRef = useRef<FraudGraphRef>(null);
  const [selectedUserId, setSelectedUserId] = useState("USR-4421");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRing, setSelectedRing] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    showUsers: true,
    showDevices: true,
    showIPs: true,
    showMerchants: true,
    riskThreshold: 0,
  });

  const getRiskLevelColor = (level: RingDetection["risk_level"]) => {
    switch (level) {
      case "critical": return "#f87171";
      case "high": return "#fbbf24";
      case "medium": return "#38bdf8";
    }
  };

  const getStatusColor = (status: RingDetection["status"]) => {
    switch (status) {
      case "active": return "#f87171";
      case "under_investigation": return "#fbbf24";
      case "neutralized": return "#34d399";
    }
  };

  // Export graph as PNG Image
  const handleExport = () => {
    if (graphRef.current) {
      graphRef.current.exportImage();
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      <FloatingHeader />
      
      <main className="pt-24 px-6 pb-12 max-w-[1800px] mx-auto">
        {/* Page Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.2)]">
              <Network className="w-5 h-5 text-[#38bdf8]" />
            </div>
            <h1 className="text-2xl font-semibold text-[#f0f4f8]">
              Fraud Ring Analysis
            </h1>
          </div>
          <p className="text-sm text-[#64748b] ml-12">
            Visualize connections between users, devices, IPs, and merchants to detect fraud rings
          </p>
        </motion.div>

        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Search & Ring List */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="col-span-12 lg:col-span-3 space-y-4 max-h-[calc(100vh-180px)] overflow-y-auto pr-2 scrollbar-thin"
          >
            {/* Search Box */}
            <div className="bg-[#151b23] rounded-xl border border-[rgba(148,163,184,0.08)] p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
                <input
                  type="text"
                  placeholder="Search user ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0f1419] border border-[rgba(148,163,184,0.1)] rounded-lg text-sm text-[#f0f4f8] placeholder:text-[#4b5563] focus:outline-none focus:border-[rgba(56,189,248,0.4)] transition-colors"
                />
              </div>
              
              {/* Quick Select Users */}
              <div className="mt-4">
                <div className="text-[10px] font-mono uppercase text-[#64748b] mb-2">
                  Quick Select
                </div>
                <div className="space-y-1.5">
                  {quickSearchUsers.map((user) => (
                    <button
                      key={user.id}
                      onClick={() => setSelectedUserId(user.id)}
                      className={cn(
                        "w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-all",
                        selectedUserId === user.id
                          ? "bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.3)]"
                          : "bg-[#0f1419] border border-transparent hover:border-[rgba(148,163,184,0.1)]"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <Users className="w-3.5 h-3.5 text-[#64748b]" />
                        <span className="text-xs font-mono text-[#f0f4f8]">{user.id}</span>
                      </div>
                      <span
                        className="text-[10px] font-mono font-semibold"
                        style={{ color: user.risk >= 80 ? "#f87171" : user.risk >= 50 ? "#fbbf24" : "#34d399" }}
                      >
                        {user.risk}%
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Detected Rings */}
            <div className="bg-[#151b23] rounded-xl border border-[rgba(148,163,184,0.08)] p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#f87171]" />
                  <span className="text-sm font-medium text-[#f0f4f8]">Detected Rings</span>
                </div>
                <span className="text-[10px] font-mono bg-[rgba(248,113,113,0.1)] text-[#f87171] px-2 py-0.5 rounded">
                  {mockRingDetections.filter(r => r.status === "active").length} ACTIVE
                </span>
              </div>

              <div className="space-y-2">
                {mockRingDetections.map((ring) => (
                  <button
                    key={ring.ring_id}
                    onClick={() => setSelectedRing(ring.ring_id)}
                    className={cn(
                      "w-full p-3 rounded-lg border text-left transition-all",
                      selectedRing === ring.ring_id
                        ? "bg-[rgba(248,113,113,0.05)] border-[rgba(248,113,113,0.3)]"
                        : "bg-[#0f1419] border-[rgba(148,163,184,0.08)] hover:border-[rgba(148,163,184,0.15)]"
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-[#f0f4f8]">{ring.ring_id}</span>
                      <span
                        className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded"
                        style={{
                          backgroundColor: `${getStatusColor(ring.status)}15`,
                          color: getStatusColor(ring.status),
                        }}
                      >
                        {ring.status.replace("_", " ")}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-[#64748b]">
                        <Users className="w-3 h-3 inline mr-1" />
                        {ring.members} members
                      </span>
                      <span
                        className="font-semibold"
                        style={{ color: getRiskLevelColor(ring.risk_level) }}
                      >
                        ${formatAmount(ring.total_fraud_amount)}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Legend Card */}
            <div className="bg-[#151b23] rounded-xl border border-[rgba(148,163,184,0.08)] p-4">
              <div className="text-[10px] font-mono uppercase text-[#64748b] mb-3">
                Entity Types
              </div>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { icon: Users, label: "Users", color: "#38bdf8" },
                  { icon: Smartphone, label: "Devices", color: "#a78bfa" },
                  { icon: Globe, label: "IP Addresses", color: "#fbbf24" },
                  { icon: CreditCard, label: "Merchants", color: "#34d399" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    <item.icon className="w-3.5 h-3.5" style={{ color: item.color }} />
                    <span className="text-[10px] text-[#94a3b8]">{item.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Main Graph Area */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="col-span-12 lg:col-span-9"
          >
            {/* Graph Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-sm text-[#64748b]">Viewing network for:</span>
                <span className="text-sm font-mono text-[#38bdf8] bg-[rgba(56,189,248,0.1)] px-2 py-1 rounded">
                  {selectedUserId}
                </span>
              </div>
              <div className="flex items-center gap-2 relative">
                <button 
                  onClick={() => setShowFilters(!showFilters)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all text-xs",
                    showFilters 
                      ? "bg-[rgba(56,189,248,0.1)] border-[rgba(56,189,248,0.3)] text-[#38bdf8]" 
                      : "bg-[#151b23] border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(148,163,184,0.2)]"
                  )}
                >
                  <Filter className="w-3.5 h-3.5" />
                  Filters
                </button>
                
                {/* Filters Dropdown */}
                {showFilters && (
                  <div className="absolute top-full right-0 mt-2 w-48 bg-[#151b23] border border-[rgba(148,163,184,0.1)] rounded-lg p-3 z-50 shadow-xl">
                    <div className="text-[10px] font-mono uppercase text-[#64748b] mb-2">Toggle Entity Types</div>
                    <div className="space-y-2">
                      {Object.entries({
                        showUsers: "Users",
                        showDevices: "Devices",
                        showIPs: "IP Addresses",
                        showMerchants: "Merchants",
                      }).map(([key, label]) => (
                        <label key={key} className="flex items-center gap-2 cursor-pointer group">
                          <input
                            type="checkbox"
                            checked={filters[key as keyof typeof filters] as boolean}
                            onChange={(e) => setFilters(prev => ({ ...prev, [key]: e.target.checked }))}
                            className="w-3.5 h-3.5 rounded border-[#4b5563] bg-[#0f1419] text-[#38bdf8] focus:ring-[#38bdf8] focus:ring-offset-0 focus:ring-offset-transparent cursor-pointer"
                          />
                          <span className="text-xs text-[#94a3b8] group-hover:text-[#f0f4f8] transition-colors">{label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                <button 
                  onClick={handleExport}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(148,163,184,0.2)] transition-all text-xs"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export
                </button>
                <button 
                  onClick={() => {
                    // Trigger a re-render of the graph to reset it
                    const currentId = selectedUserId;
                    setSelectedUserId("");
                    setTimeout(() => setSelectedUserId(currentId), 10);
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(148,163,184,0.2)] transition-all text-xs"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh
                </button>
              </div>
            </div>

            {/* Graph Component */}
            <div className="h-[700px] rounded-xl overflow-hidden">
              {selectedUserId && (
                <FraudGraph 
                  ref={graphRef}
                  userId={selectedUserId} 
                  className="w-full h-full"
                  filters={filters}
                />
              )}
            </div>

            {/* Graph Insights Footer */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="mt-4 grid grid-cols-4 gap-4"
            >
              {[
                { label: "Shared Devices", value: "2", icon: Smartphone, color: "#a78bfa" },
                { label: "Common IPs", value: "3", icon: Globe, color: "#fbbf24" },
                { label: "Connected Users", value: "4", icon: Users, color: "#38bdf8" },
                { label: "Fraud Probability", value: "87%", icon: AlertTriangle, color: "#f87171" },
              ].map((stat, i) => (
                <div
                  key={stat.label}
                  className="bg-[#151b23] rounded-lg border border-[rgba(148,163,184,0.08)] p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <stat.icon className="w-4 h-4" style={{ color: stat.color }} />
                    <span
                      className="text-lg font-mono font-semibold"
                      style={{ color: stat.color }}
                    >
                      {stat.value}
                    </span>
                  </div>
                  <div className="text-[10px] text-[#64748b] uppercase font-mono">
                    {stat.label}
                  </div>
                </div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
