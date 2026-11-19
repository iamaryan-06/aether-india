"use client";

import { useEffect, useState } from "react";
import { ApprovalRequest } from "@/types";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { formatINR } from "@/lib/utils";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  User,
  ArrowRight,
  CreditCard,
  FileText,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";

export default function AdminApprovalsPage() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState("PENDING_ADMIN");
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [adminNotes, setAdminNotes] = useState<Record<number, string>>({});
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const { user, loginAsDemoAdmin } = useAuthStore();

  const loadApprovals = async (status = statusFilter) => {
    setIsLoading(true);
    try {
      if (!user || user.role !== "admin") {
        await loginAsDemoAdmin();
      }
      const data = await api.getAdminApprovals(status);
      setApprovals(data);
    } catch (err) {
      console.error("Failed to load approvals", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals(statusFilter);
  }, [user, statusFilter]);

  const handleDecision = async (approvalId: number, action: "APPROVE" | "REJECT") => {
    const notes = adminNotes[approvalId] || (action === "APPROVE" ? "Approved by Operations Head" : "Rejected by Operations Head");

    if (action === "REJECT" && !adminNotes[approvalId]) {
      const promptNotes = prompt("Please provide a reason for rejecting this refund request:");
      if (!promptNotes) return;
      adminNotes[approvalId] = promptNotes;
    }

    setActionLoading(approvalId);
    setActionFeedback(null);
    try {
      const res = await api.actOnApproval(approvalId, action, adminNotes[approvalId]);
      setActionFeedback(
        `Ticket #${approvalId} ${action === "APPROVE" ? "APPROVED" : "REJECTED"} successfully. Customer notified.`
      );
      await loadApprovals();
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black font-mono tracking-tight text-white uppercase flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-street-amber" />
            Human-in-the-Loop (HITL) Approval Queue
          </h1>
          <p className="text-xs font-mono text-aether-400 mt-1">
            Requests exceeding the ₹5,000 auto-approval threshold or flagged for policy exceptions.
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-aether-900 border border-aether-800 text-xs font-mono">
          {["PENDING_ADMIN", "APPROVED", "REJECTED", "ALL"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                statusFilter === st
                  ? "bg-white text-black font-bold shadow"
                  : "text-aether-400 hover:text-white"
              }`}
            >
              {st === "PENDING_ADMIN" ? "Pending Review" : st}
            </button>
          ))}
        </div>
      </div>

      {actionFeedback && (
        <div className="p-4 rounded-xl bg-street-emerald/10 border border-street-emerald/30 text-street-emerald font-mono text-xs flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> {actionFeedback}
          </span>
          <button onClick={() => setActionFeedback(null)} className="text-xs hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Ticket Cards */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-64 rounded-2xl bg-aether-900/40 border border-aether-800/60 animate-pulse" />
          ))}
        </div>
      ) : approvals.length === 0 ? (
        <div className="py-20 text-center font-mono text-aether-500 rounded-2xl bg-aether-900/40 border border-aether-800 p-8 space-y-2">
          <CheckCircle2 className="w-8 h-8 text-street-emerald mx-auto" />
          <p className="text-sm font-bold text-white uppercase">Queue is Clear</p>
          <p className="text-xs text-aether-400">No {statusFilter.replace("_", " ")} tickets requiring human review.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {approvals.map((req) => {
            const isPending = req.status === "PENDING_ADMIN";
            const isApproved = req.status === "APPROVED";
            const isRejected = req.status === "REJECTED";

            return (
              <div
                key={req.id}
                className={`rounded-2xl border p-6 space-y-5 shadow-2xl transition-all ${
                  isPending
                    ? "bg-aether-900/80 border-street-amber/40 shadow-street-amber/5"
                    : "bg-aether-900/40 border-aether-800"
                }`}
              >
                {/* Card Top Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-aether-850 pb-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="px-2.5 py-0.5 rounded-lg text-xs font-mono font-bold bg-aether-850 border border-aether-700 text-white">
                      Ticket #{req.id}
                    </span>
                    <span className="text-sm font-black font-mono text-white">
                      Order {req.order_number}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-street-red/20 text-street-red border border-street-red/30 uppercase">
                      {req.action_type.replace(/_/g, " ")}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-aether-400">Review Amount:</span>
                    <span className="text-lg font-black text-white font-mono">{formatINR(req.amount_inr)}</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        isApproved
                          ? "bg-street-emerald/20 text-street-emerald"
                          : isRejected
                          ? "bg-street-red/20 text-street-red"
                          : "bg-street-amber/20 text-street-amber animate-pulse"
                      }`}
                    >
                      {req.status}
                    </span>
                  </div>
                </div>

                {/* Stated Customer Reason & User Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3.5 rounded-xl bg-aether-950 border border-aether-850 space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-aether-500 font-bold block">
                      Customer Stated Reason:
                    </span>
                    <p className="text-white leading-relaxed">"{req.reason}"</p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-aether-950 border border-aether-850 space-y-1">
                    <span className="text-[10px] uppercase tracking-wider text-aether-500 font-bold block">
                      Case Metadata:
                    </span>
                    <p className="text-aether-300">
                      User ID: {req.user_id} (Aarav Sharma) • Amount: {formatINR(req.amount_inr)}
                    </p>
                    <p className="text-aether-500 text-[11px]">
                      Created: {new Date(req.created_at).toLocaleString("en-IN")}
                    </p>
                  </div>
                </div>

                {/* AI Multi-Agent Synthesized Context Summary */}
                <div className="p-4 rounded-xl bg-aether-950/80 border border-street-cyan/20 space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-street-cyan">
                    <Sparkles className="w-4 h-4" />
                    <span>Multi-Agent Synthesized Case Brief</span>
                  </div>
                  <p className="text-xs font-mono text-aether-300 leading-relaxed whitespace-pre-line">
                    {req.ai_summary}
                  </p>
                </div>

                {/* Admin Notes if Resolved */}
                {req.admin_notes && (
                  <div className="p-3.5 rounded-xl bg-aether-850/60 border border-aether-800 text-xs font-mono text-aether-300">
                    <span className="text-[10px] uppercase text-aether-500 font-bold block">Operations Head Notes:</span>
                    <p className="mt-0.5">{req.admin_notes}</p>
                  </div>
                )}

                {/* Action Row (Only for PENDING_ADMIN) */}
                {isPending && (
                  <div className="pt-2 border-t border-aether-850 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
                    <input
                      type="text"
                      placeholder="Add operational notes or authorization reference (optional)..."
                      value={adminNotes[req.id] || ""}
                      onChange={(e) => setAdminNotes((prev) => ({ ...prev, [req.id]: e.target.value }))}
                      className="flex-1 bg-aether-950 border border-aether-800 focus:border-white rounded-xl px-4 py-2.5 text-xs text-white placeholder-aether-600 focus:outline-none transition-colors font-mono"
                    />

                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        onClick={() => handleDecision(req.id, "REJECT")}
                        disabled={actionLoading === req.id}
                        className="px-4 py-2.5 rounded-xl bg-street-red/10 hover:bg-street-red/20 border border-street-red/30 text-street-red font-mono text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <XCircle className="w-4 h-4" /> Reject Request
                      </button>

                      <button
                        onClick={() => handleDecision(req.id, "APPROVE")}
                        disabled={actionLoading === req.id}
                        className="px-5 py-2.5 rounded-xl bg-street-emerald hover:bg-street-emerald/90 text-black font-mono text-xs font-black transition-all shadow-lg disabled:opacity-50 flex items-center gap-1.5 hover:scale-[1.02]"
                      >
                        <CheckCircle2 className="w-4 h-4 text-black" /> Approve &amp; Issue {formatINR(req.amount_inr)} Refund
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
