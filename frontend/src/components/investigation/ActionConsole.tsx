// ============================================================================
// SENTINEL ACTION CONSOLE
// Manual override controls for fraud investigation
// ============================================================================

"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  UserX,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Lock,
  Unlock,
  MessageSquare,
  Send,
  Loader2,
} from "lucide-react";

interface ActionConsoleProps {
  txnId: string;
  currentStatus: string;
  onAction?: (action: string, notes?: string) => void;
  className?: string;
}

interface ActionButton {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  confirmRequired: boolean;
}

const actions: ActionButton[] = [
  {
    id: "confirm_fraud",
    label: "Confirm Fraud",
    description: "Mark as verified fraudulent transaction",
    icon: <ShieldAlert className="w-5 h-5" />,
    color: "#f87171",
    bgColor: "rgba(248,113,113,0.1)",
    borderColor: "rgba(248,113,113,0.3)",
    confirmRequired: true,
  },
  {
    id: "false_positive",
    label: "False Positive",
    description: "Mark as legitimate transaction",
    icon: <ShieldCheck className="w-5 h-5" />,
    color: "#34d399",
    bgColor: "rgba(52,211,153,0.1)",
    borderColor: "rgba(52,211,153,0.3)",
    confirmRequired: true,
  },
  {
    id: "freeze_account",
    label: "Freeze Account",
    description: "Temporarily suspend all account activity",
    icon: <Lock className="w-5 h-5" />,
    color: "#fbbf24",
    bgColor: "rgba(251,191,36,0.1)",
    borderColor: "rgba(251,191,36,0.3)",
    confirmRequired: true,
  },
  {
    id: "unblock",
    label: "Unblock",
    description: "Allow transaction to proceed",
    icon: <Unlock className="w-5 h-5" />,
    color: "#38bdf8",
    bgColor: "rgba(56,189,248,0.1)",
    borderColor: "rgba(56,189,248,0.3)",
    confirmRequired: true,
  },
];

export function ActionConsole({ txnId, currentStatus, onAction, className }: ActionConsoleProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [completedAction, setCompletedAction] = useState<string | null>(null);

  const handleActionClick = (actionId: string) => {
    const action = actions.find((a) => a.id === actionId);
    if (action?.confirmRequired) {
      setSelectedAction(actionId);
    } else {
      executeAction(actionId);
    }
  };

  const executeAction = async (actionId: string) => {
    setIsProcessing(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    onAction?.(actionId, notes);
    setCompletedAction(actionId);
    setIsProcessing(false);
    setSelectedAction(null);
    setNotes("");
    
    // Clear completed state after animation
    setTimeout(() => setCompletedAction(null), 3000);
  };

  const cancelAction = () => {
    setSelectedAction(null);
    setNotes("");
  };

  return (
    <div className={cn("bg-[#151b23] border border-[rgba(148,163,184,0.08)] rounded-xl overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 bg-[#0f1419] border-b border-[rgba(148,163,184,0.08)]">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-[#fbbf24]" />
          <h3
            className="text-[14px] font-semibold text-[#f0f4f8]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Action Console
          </h3>
        </div>
        <div className="text-xs font-mono text-[#64748b]">
          Status: <span className="text-[#fbbf24]">{currentStatus.toUpperCase()}</span>
        </div>
      </div>

      {/* Success Banner */}
      <AnimatePresence>
        {completedAction && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-[rgba(52,211,153,0.1)] border-b border-[rgba(52,211,153,0.2)] px-5 py-3"
          >
            <div className="flex items-center gap-2 text-[#34d399]">
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">
                Action "{actions.find((a) => a.id === completedAction)?.label}" executed successfully
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action Buttons Grid */}
      <div className="p-5">
        <div className="grid grid-cols-2 gap-3">
          {actions.map((action) => (
            <motion.button
              key={action.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleActionClick(action.id)}
              disabled={isProcessing || selectedAction !== null}
              className={cn(
                "relative flex flex-col items-start p-4 rounded-xl border transition-all",
                "hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed",
                selectedAction === action.id
                  ? "ring-2 ring-offset-2 ring-offset-[#151b23]"
                  : ""
              )}
              style={{
                backgroundColor: action.bgColor,
                borderColor: action.borderColor,
                ...(selectedAction === action.id && { ringColor: action.color }),
              }}
            >
              <div style={{ color: action.color }} className="mb-2">
                {action.icon}
              </div>
              <div className="text-sm font-semibold text-[#f0f4f8]">{action.label}</div>
              <div className="text-[11px] text-[#64748b] mt-1">{action.description}</div>
            </motion.button>
          ))}
        </div>

        {/* Confirmation Dialog */}
        <AnimatePresence>
          {selectedAction && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="mt-5 p-4 bg-[#0f1419] rounded-xl border border-[rgba(148,163,184,0.1)]"
            >
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-4 h-4 text-[#fbbf24]" />
                <span className="text-sm font-semibold text-[#f0f4f8]">Confirm Action</span>
              </div>
              <p className="text-xs text-[#64748b] mb-4">
                You are about to execute "{actions.find((a) => a.id === selectedAction)?.label}" on transaction{" "}
                <span className="text-[#38bdf8] font-mono">{txnId}</span>. This action will be logged and cannot be easily undone.
              </p>

              {/* Notes Input */}
              <div className="mb-4">
                <label className="text-[10px] font-mono uppercase text-[#64748b] mb-1.5 block">
                  Investigation Notes (Optional)
                </label>
                <div className="relative">
                  <MessageSquare className="absolute left-3 top-3 w-4 h-4 text-[#64748b]" />
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Add notes for audit trail..."
                    className="w-full pl-10 pr-4 py-2.5 bg-[#151b23] border border-[rgba(148,163,184,0.1)] rounded-lg text-sm text-[#f0f4f8] placeholder:text-[#64748b] focus:outline-none focus:border-[rgba(56,189,248,0.4)] resize-none"
                    rows={2}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => executeAction(selectedAction)}
                  disabled={isProcessing}
                  className={cn(
                    "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg font-medium text-sm transition-all",
                    "bg-[rgba(248,113,113,0.15)] text-[#f87171] border border-[rgba(248,113,113,0.3)]",
                    "hover:bg-[rgba(248,113,113,0.25)] disabled:opacity-50"
                  )}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Execute Action
                    </>
                  )}
                </button>
                <button
                  onClick={cancelAction}
                  disabled={isProcessing}
                  className="px-4 py-2.5 rounded-lg text-sm font-medium text-[#64748b] border border-[rgba(148,163,184,0.1)] hover:bg-[rgba(148,163,184,0.1)] hover:text-[#f0f4f8] transition-all disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#0f1419] border-t border-[rgba(148,163,184,0.08)]">
        <div className="text-[10px] font-mono text-[#64748b]">
          All actions are logged for compliance audit
        </div>
        <div className="text-[10px] font-mono text-[#64748b]">
          TXN: {txnId.slice(0, 16)}
        </div>
      </div>
    </div>
  );
}

export default ActionConsole;
