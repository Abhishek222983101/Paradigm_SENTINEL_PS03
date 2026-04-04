// ============================================================================
// SENTINEL FRAUD GRAPH COMPONENT
// Interactive Cytoscape visualization of fraud rings and connections
// ============================================================================

"use client";

import { useEffect, useRef, useState, useCallback, useMemo, forwardRef, useImperativeHandle } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  User,
  Smartphone,
  Globe,
  CreditCard,
  X,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Download,
  Eye,
  AlertTriangle,
  DollarSign,
  Clock,
  Network,
} from "lucide-react";

// Cytoscape types
interface CytoscapeNode {
  data: {
    id: string;
    label: string;
    type: "user" | "device" | "ip" | "merchant" | "transaction";
    risk?: number;
    details?: Record<string, unknown>;
  };
}

interface CytoscapeEdge {
  data: {
    id: string;
    source: string;
    target: string;
    type: "transaction" | "login" | "shared_device" | "shared_ip";
    weight?: number;
    amount?: number;
  };
}

interface GraphData {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
}

interface FraudGraphProps {
  userId?: string;
  graphData?: GraphData;
  className?: string;
  filters?: {
    showUsers: boolean;
    showDevices: boolean;
    showIPs: boolean;
    showMerchants: boolean;
    riskThreshold: number;
  };
}

// ============================================================================
// MOCK GRAPH DATA
// ============================================================================

const generateMockGraphData = (userId: string): GraphData => {
  return {
    nodes: [
      // Central user
      { data: { id: userId, label: userId, type: "user", risk: 85, details: { account_age: 847, total_txns: 342 } } },
      // Connected users (potential fraud ring)
      { data: { id: "USR-7892", label: "USR-7892", type: "user", risk: 72, details: { account_age: 45, total_txns: 23 } } },
      { data: { id: "USR-1156", label: "USR-1156", type: "user", risk: 91, details: { account_age: 12, total_txns: 8 } } },
      { data: { id: "USR-3341", label: "USR-3341", type: "user", risk: 68, details: { account_age: 234, total_txns: 156 } } },
      // Devices
      { data: { id: "DEV-882", label: "iPhone 15 Pro", type: "device", risk: 45 } },
      { data: { id: "DEV-NEW-X892", label: "Unknown Device", type: "device", risk: 95 } },
      { data: { id: "DEV-441", label: "MacBook Pro", type: "device", risk: 30 } },
      // IPs
      { data: { id: "IP-197.210", label: "197.210.XX.XX", type: "ip", risk: 88, details: { location: "Lagos, Nigeria", vpn: true } } },
      { data: { id: "IP-192.168", label: "192.168.XX.XX", type: "ip", risk: 25, details: { location: "New York, US", vpn: false } } },
      { data: { id: "IP-PROXY", label: "TOR Exit Node", type: "ip", risk: 99, details: { location: "Unknown", vpn: true } } },
      // Merchants
      { data: { id: "MERCH-001", label: "Luxury Electronics", type: "merchant", risk: 75 } },
      { data: { id: "MERCH-002", label: "Crypto Exchange", type: "merchant", risk: 82 } },
    ],
    edges: [
      // User to device connections
      { data: { id: "e1", source: userId, target: "DEV-882", type: "login" } },
      { data: { id: "e2", source: userId, target: "DEV-NEW-X892", type: "login" } },
      { data: { id: "e3", source: "USR-7892", target: "DEV-NEW-X892", type: "shared_device", weight: 3 } },
      { data: { id: "e4", source: "USR-1156", target: "DEV-NEW-X892", type: "shared_device", weight: 2 } },
      // User to IP
      { data: { id: "e5", source: userId, target: "IP-197.210", type: "login" } },
      { data: { id: "e6", source: "USR-7892", target: "IP-197.210", type: "shared_ip", weight: 5 } },
      { data: { id: "e7", source: "USR-1156", target: "IP-PROXY", type: "login" } },
      { data: { id: "e8", source: "USR-3341", target: "IP-192.168", type: "login" } },
      // Transactions
      { data: { id: "e9", source: userId, target: "MERCH-001", type: "transaction", amount: 15420 } },
      { data: { id: "e10", source: "USR-7892", target: "MERCH-001", type: "transaction", amount: 8750 } },
      { data: { id: "e11", source: "USR-1156", target: "MERCH-002", type: "transaction", amount: 45000 } },
      { data: { id: "e12", source: userId, target: "USR-7892", type: "transaction", amount: 2500 } },
      // More connections
      { data: { id: "e13", source: "USR-3341", target: "DEV-441", type: "login" } },
      { data: { id: "e14", source: userId, target: "IP-192.168", type: "login" } },
    ],
  };
};

// ============================================================================
// NODE DETAIL DRAWER
// ============================================================================

interface NodeDetailDrawerProps {
  node: CytoscapeNode["data"] | null;
  onClose: () => void;
}

function NodeDetailDrawer({ node, onClose }: NodeDetailDrawerProps) {
  if (!node) return null;

  const getIcon = () => {
    switch (node.type) {
      case "user": return <User className="w-5 h-5" />;
      case "device": return <Smartphone className="w-5 h-5" />;
      case "ip": return <Globe className="w-5 h-5" />;
      case "merchant": return <CreditCard className="w-5 h-5" />;
      default: return <Network className="w-5 h-5" />;
    }
  };

  const getTypeColor = () => {
    switch (node.type) {
      case "user": return "#38bdf8";
      case "device": return "#a78bfa";
      case "ip": return "#fbbf24";
      case "merchant": return "#34d399";
      default: return "#64748b";
    }
  };

  const riskColor = (node.risk ?? 0) >= 80 ? "#f87171" : (node.risk ?? 0) >= 50 ? "#fbbf24" : "#34d399";

  return (
    <motion.div
      initial={{ x: 300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 300, opacity: 0 }}
      className="absolute top-0 right-0 w-80 h-full bg-[#151b23] border-l border-[rgba(148,163,184,0.1)] z-10 overflow-hidden flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
        <div className="flex items-center gap-2">
          <div style={{ color: getTypeColor() }}>{getIcon()}</div>
          <span className="text-sm font-semibold text-[#f0f4f8]">Node Details</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* ID */}
        <div>
          <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Identifier</div>
          <div className="text-[#38bdf8] font-mono text-sm">{node.id}</div>
        </div>

        {/* Type Badge */}
        <div>
          <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Type</div>
          <span
            className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium"
            style={{ backgroundColor: `${getTypeColor()}20`, color: getTypeColor() }}
          >
            {getIcon()}
            {node.type.charAt(0).toUpperCase() + node.type.slice(1)}
          </span>
        </div>

        {/* Risk Score */}
        {node.risk !== undefined && (
          <div>
            <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Risk Score</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-[#0f1419] rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${node.risk}%` }}
                  className="h-full rounded-full"
                  style={{ backgroundColor: riskColor }}
                />
              </div>
              <span className="text-sm font-mono font-semibold" style={{ color: riskColor }}>
                {node.risk}%
              </span>
            </div>
          </div>
        )}

        {/* Label */}
        <div>
          <div className="text-[10px] font-mono uppercase text-[#64748b] mb-1">Label</div>
          <div className="text-[#f0f4f8] text-sm">{node.label}</div>
        </div>

        {/* Additional Details */}
        {node.details && Object.keys(node.details).length > 0 && (
          <div className="pt-3 border-t border-[rgba(148,163,184,0.08)]">
            <div className="text-[10px] font-mono uppercase text-[#64748b] mb-2">Additional Info</div>
            <div className="space-y-2">
              {Object.entries(node.details).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-xs text-[#64748b]">{key.replace(/_/g, " ")}</span>
                  <span className="text-xs font-mono text-[#f0f4f8]">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 bg-[#0f1419] border-t border-[rgba(148,163,184,0.08)]">
        <button className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.25)] text-[#38bdf8] text-sm font-medium hover:bg-[rgba(56,189,248,0.15)] transition-all">
          <Eye className="w-4 h-4" />
          View Full Profile
        </button>
      </div>
    </motion.div>
  );
}

// ============================================================================
// MAIN FRAUD GRAPH COMPONENT
// ============================================================================

export interface FraudGraphRef {
  exportImage: () => void;
}

export const FraudGraph = forwardRef<FraudGraphRef, FraudGraphProps>(({ 
  userId = "USR-4421", 
  graphData, 
  className,
  filters = {
    showUsers: true,
    showDevices: true,
    showIPs: true,
    showMerchants: true,
    riskThreshold: 0,
  }
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);
  const layoutRef = useRef<any>(null);
  const mountedRef = useRef(true);
  const [selectedNode, setSelectedNode] = useState<CytoscapeNode["data"] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({ nodes: 0, edges: 0, riskNodes: 0 });

  useImperativeHandle(ref, () => ({
    exportImage: () => {
      if (!cyRef.current) return;
      // Cytoscape png() exports the current graph view
      const b64 = cyRef.current.png({ output: 'base64uri', bg: '#0a0e14', full: true, scale: 2 });
      const a = document.createElement("a");
      a.href = b64;
      a.download = `fraud-ring-${userId}-${Date.now()}.png`;
      a.click();
    }
  }));

  // Memoize data to prevent re-renders from triggering layout recalculation
  const data = useMemo(() => {
    const rawData = graphData || generateMockGraphData(userId);
    
    // Apply filters
    const filteredNodes = rawData.nodes.filter(node => {
      // Risk filter
      if ((node.data.risk ?? 0) < filters.riskThreshold) return false;
      
      // Type filters
      if (!filters.showUsers && node.data.type === "user") return false;
      if (!filters.showDevices && node.data.type === "device") return false;
      if (!filters.showIPs && node.data.type === "ip") return false;
      if (!filters.showMerchants && node.data.type === "merchant") return false;
      
      return true;
    });

    const validNodeIds = new Set(filteredNodes.map(n => n.data.id));

    // Filter edges to only include those between valid nodes
    const filteredEdges = rawData.edges.filter(edge => 
      validNodeIds.has(edge.data.source) && validNodeIds.has(edge.data.target)
    );

    return {
      nodes: filteredNodes,
      edges: filteredEdges,
    };
  }, [userId, graphData, filters]);

  // Initialize Cytoscape
  useEffect(() => {
    mountedRef.current = true;
    
    const initCytoscape = async () => {
      if (!containerRef.current || !mountedRef.current) return;

      const cytoscape = (await import("cytoscape")).default;

      // Clear existing instance
      if (cyRef.current) {
        if (layoutRef.current) {
          layoutRef.current.stop();
        }
        cyRef.current.destroy();
        cyRef.current = null;
      }

      if (!mountedRef.current) return;

      const cy = cytoscape({
        container: containerRef.current,
        elements: [...data.nodes, ...data.edges],
        style: [
          // Node styles by type
          {
            selector: 'node[type="user"]',
            style: {
              "background-color": "#0f1419",
              "border-width": 3,
              "border-color": "#38bdf8",
              label: "data(label)",
              "text-valign": "bottom",
              "text-margin-y": 8,
              color: "#94a3b8",
              "font-size": "10px",
              "font-family": "monospace",
              width: 40,
              height: 40,
            },
          },
          {
            selector: 'node[type="device"]',
            style: {
              "background-color": "#0f1419",
              "border-width": 3,
              "border-color": "#a78bfa",
              label: "data(label)",
              "text-valign": "bottom",
              "text-margin-y": 8,
              color: "#94a3b8",
              "font-size": "9px",
              "font-family": "monospace",
              width: 35,
              height: 35,
            },
          },
          {
            selector: 'node[type="ip"]',
            style: {
              "background-color": "#0f1419",
              "border-width": 3,
              "border-color": "#fbbf24",
              label: "data(label)",
              "text-valign": "bottom",
              "text-margin-y": 8,
              color: "#94a3b8",
              "font-size": "9px",
              "font-family": "monospace",
              width: 35,
              height: 35,
            },
          },
          {
            selector: 'node[type="merchant"]',
            style: {
              "background-color": "#0f1419",
              "border-width": 3,
              "border-color": "#34d399",
              label: "data(label)",
              "text-valign": "bottom",
              "text-margin-y": 8,
              color: "#94a3b8",
              "font-size": "9px",
              "font-family": "monospace",
              width: 35,
              height: 35,
            },
          },
          // High risk nodes
          {
            selector: "node[risk >= 80]",
            style: {
              "border-color": "#f87171",
              "border-width": 4,
            },
          },
          // Edge styles
          {
            selector: 'edge[type="transaction"]',
            style: {
              width: 2,
              "line-color": "#f87171",
              "target-arrow-color": "#f87171",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              opacity: 0.7,
            },
          },
          {
            selector: 'edge[type="login"]',
            style: {
              width: 1.5,
              "line-color": "#38bdf8",
              "line-style": "dashed",
              "curve-style": "bezier",
              opacity: 0.6,
            },
          },
          {
            selector: 'edge[type="shared_device"]',
            style: {
              width: 2,
              "line-color": "#a78bfa",
              "curve-style": "bezier",
              opacity: 0.8,
            },
          },
          {
            selector: 'edge[type="shared_ip"]',
            style: {
              width: 2,
              "line-color": "#fbbf24",
              "curve-style": "bezier",
              opacity: 0.8,
            },
          },
          // Selected/hover states
          {
            selector: "node:selected",
            style: {
              "border-width": 5,
              "border-color": "#f0f4f8",
              "background-color": "#1a222d",
            },
          },
          {
            selector: "node.hover",
            style: {
              "border-width": 4,
              "background-color": "#1a222d",
            },
          },
          {
            selector: "edge.highlighted",
            style: {
              width: 4,
              opacity: 1,
            },
          },
        ],
        layout: {
          name: "preset", // Use preset initially (no animation)
        },
        minZoom: 0.3,
        maxZoom: 3,
      });

      // Run layout after creation (non-animated for initial render)
      const layout = cy.layout({
        name: "cose",
        animate: false, // No animation on initial load to avoid cleanup issues
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 100,
        padding: 50,
      });
      layout.run();

      // Event handlers
      cy.on("tap", "node", (evt: any) => {
        const node = evt.target;
        setSelectedNode(node.data());
      });

      cy.on("tap", (evt: any) => {
        if (evt.target === cy) {
          setSelectedNode(null);
        }
      });

      cy.on("mouseover", "node", (evt: any) => {
        const node = evt.target;
        node.addClass("hover");
        // Highlight connected edges
        node.connectedEdges().addClass("highlighted");
      });

      cy.on("mouseout", "node", (evt: any) => {
        const node = evt.target;
        node.removeClass("hover");
        node.connectedEdges().removeClass("highlighted");
      });

      cyRef.current = cy;

      // Calculate stats
      const riskNodes = data.nodes.filter((n) => (n.data.risk ?? 0) >= 80).length;
      setStats({
        nodes: data.nodes.length,
        edges: data.edges.length,
        riskNodes,
      });

      setIsLoading(false);
    };

    initCytoscape();

    return () => {
      mountedRef.current = false;
      if (layoutRef.current) {
        try {
          layoutRef.current.stop();
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      if (cyRef.current) {
        try {
          cyRef.current.destroy();
        } catch (e) {
          // Ignore cleanup errors
        }
        cyRef.current = null;
      }
    };
  }, [data]);

  // Control functions
  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.3);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() / 1.3);
  const handleFit = () => cyRef.current?.fit(undefined, 50);
  const handleRefresh = () => {
    if (!cyRef.current || !mountedRef.current) return;
    // Stop any existing layout
    if (layoutRef.current) {
      try {
        layoutRef.current.stop();
      } catch (e) {
        // Ignore
      }
      layoutRef.current = null;
    }
    // Use non-animated layout to avoid cleanup race conditions
    const layout = cyRef.current.layout({ 
      name: "cose", 
      animate: false,
      nodeRepulsion: () => 8000,
      idealEdgeLength: () => 100,
      padding: 50,
    });
    layout.run();
  };

  return (
    <div className={cn("relative bg-[#0a0e14] rounded-xl overflow-hidden border border-[rgba(148,163,184,0.08)]", className)}>
      {/* Graph Container */}
      <div ref={containerRef} className="w-full h-full min-h-[500px]" />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-[#0a0e14] flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          >
            <Network className="w-8 h-8 text-[#38bdf8]" />
          </motion.div>
        </div>
      )}

      {/* Controls */}
      <div className="absolute top-4 left-4 flex flex-col gap-2">
        <button
          onClick={handleZoomIn}
          className="p-2 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(56,189,248,0.3)] transition-all"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(56,189,248,0.3)] transition-all"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleFit}
          className="p-2 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(56,189,248,0.3)] transition-all"
          title="Fit to View"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={handleRefresh}
          className="p-2 rounded-lg bg-[#151b23] border border-[rgba(148,163,184,0.1)] text-[#64748b] hover:text-[#f0f4f8] hover:border-[rgba(56,189,248,0.3)] transition-all"
          title="Re-layout"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-[#151b23]/90 backdrop-blur-sm border border-[rgba(148,163,184,0.1)] rounded-lg p-3">
        <div className="text-[10px] font-mono uppercase text-[#64748b] mb-2">Legend</div>
        <div className="space-y-1.5">
          {[
            { color: "#38bdf8", label: "User" },
            { color: "#a78bfa", label: "Device" },
            { color: "#fbbf24", label: "IP Address" },
            { color: "#34d399", label: "Merchant" },
            { color: "#f87171", label: "High Risk" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full border-2" style={{ borderColor: item.color, backgroundColor: "#0f1419" }} />
              <span className="text-[10px] text-[#94a3b8]">{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-[#151b23]/90 backdrop-blur-sm border border-[rgba(148,163,184,0.1)] rounded-lg p-3">
        <div className="text-[10px] font-mono uppercase text-[#64748b] mb-2">Graph Stats</div>
        <div className="space-y-1">
          <div className="flex justify-between gap-4 text-xs">
            <span className="text-[#64748b]">Nodes</span>
            <span className="text-[#38bdf8] font-mono">{stats.nodes}</span>
          </div>
          <div className="flex justify-between gap-4 text-xs">
            <span className="text-[#64748b]">Edges</span>
            <span className="text-[#a78bfa] font-mono">{stats.edges}</span>
          </div>
          <div className="flex justify-between gap-4 text-xs">
            <span className="text-[#64748b]">High Risk</span>
            <span className="text-[#f87171] font-mono">{stats.riskNodes}</span>
          </div>
        </div>
      </div>

      {/* Node Detail Drawer */}
      <AnimatePresence>
        {selectedNode && (
          <NodeDetailDrawer node={selectedNode} onClose={() => setSelectedNode(null)} />
        )}
      </AnimatePresence>
    </div>
  );
});

export default FraudGraph;
