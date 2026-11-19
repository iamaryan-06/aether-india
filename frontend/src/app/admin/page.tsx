"use client";

import { useEffect, useState } from "react";
import { AdminKPISummary, Order, AgentActionLog } from "@/types";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { formatINR } from "@/lib/utils";
import {
  IndianRupee,
  Package,
  ShieldAlert,
  Bot,
  ArrowRight,
  TrendingUp,
  Sparkles,
  Truck,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";

export default function AdminDashboardPage() {
  const [kpis, setKpis] = useState<AdminKPISummary | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [recentLogs, setRecentLogs] = useState<AgentActionLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { user, loginAsDemoAdmin } = useAuthStore();

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        if (!user || user.role !== "admin") {
          await loginAsDemoAdmin();
        }
        const [kpiData, ordersData, logsData] = await Promise.all([
          api.getAdminKPIs(),
          api.getAdminOrders(),
          api.getAdminAgentLogs(undefined, 5),
        ]);
        setKpis(kpiData);
        setRecentOrders(ordersData.slice(0, 5));
        setRecentLogs(logsData);
      } catch (err) {
        console.error("Failed to load admin dashboard data", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [user]);

  return (
    <div className="space-y-8">
      {/* Pending HITL High-Value Refund Alert Banner */}
      {kpis && kpis.pending_approvals_count > 0 && (
        <div className="p-4 sm:p-5 rounded-2xl bg-street-amber/10 border border-street-amber/40 text-white font-mono flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-street-amber/20 text-street-amber border border-street-amber/40 shrink-0">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-black uppercase text-street-amber tracking-wider">
                  Action Required: {kpis.pending_approvals_count} Pending Review(s)
                </span>
                <span className="px-2 py-0.5 text-[9px] bg-street-amber/20 text-street-amber rounded-full font-bold">
                  &gt; ₹5,000 Threshold
                </span>
              </div>
              <p className="text-xs text-aether-300 mt-0.5">
                Order AETH-1003 (Apex 3-Layer Gore-Tex Jacket, ₹7,999) has been flagged by Agent 3 for Operations Head authorization.
              </p>
            </div>
          </div>

          <Link
            href="/admin/approvals"
            className="px-4 py-2 rounded-xl bg-street-amber hover:bg-street-amber/90 text-black text-xs font-bold transition-all shadow-md shrink-0 flex items-center gap-1.5"
          >
            Review in HITL Queue <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* KPI 4-Card Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Revenue in INR */}
        <div className="p-5 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-2">
          <div className="flex items-center justify-between text-aether-400">
            <span className="text-[11px] font-mono uppercase tracking-wider">Gross Platform Revenue</span>
            <div className="p-1.5 rounded-lg bg-street-emerald/10 text-street-emerald">
              <IndianRupee className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-mono tracking-tight text-white">
            {kpis?.total_revenue_formatted || "₹0"}
          </div>
          <div className="text-[10px] font-mono text-street-emerald flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Live SQLite orders data
          </div>
        </div>

        {/* Metric 2: Total Orders */}
        <div className="p-5 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-2">
          <div className="flex items-center justify-between text-aether-400">
            <span className="text-[11px] font-mono uppercase tracking-wider">Total Customer Orders</span>
            <div className="p-1.5 rounded-lg bg-street-cyan/10 text-street-cyan">
              <Package className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-mono tracking-tight text-white">
            {kpis?.total_orders_count ?? 0}
          </div>
          <div className="text-[10px] font-mono text-aether-400">
            Active shipments via BlueDart &amp; Delhivery
          </div>
        </div>

        {/* Metric 3: AI Resolved vs Human Escalated */}
        <div className="p-5 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-2">
          <div className="flex items-center justify-between text-aether-400">
            <span className="text-[11px] font-mono uppercase tracking-wider">AI Autonomous Resolution</span>
            <div className="p-1.5 rounded-lg bg-street-purple/10 text-street-purple">
              <Bot className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-mono tracking-tight text-white flex items-baseline gap-1.5">
            <span>{kpis?.ai_auto_resolved_count ?? 0}</span>
            <span className="text-xs text-aether-500 font-normal">
              / {kpis?.human_escalated_count ?? 0} escalated
            </span>
          </div>
          <div className="text-[10px] font-mono text-street-purple">
            4-Agent LangGraph supervisor routing
          </div>
        </div>

        {/* Metric 4: Pending Approvals */}
        <div className="p-5 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-2">
          <div className="flex items-center justify-between text-aether-400">
            <span className="text-[11px] font-mono uppercase tracking-wider">HITL Pending Queue</span>
            <div className="p-1.5 rounded-lg bg-street-amber/10 text-street-amber">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black font-mono tracking-tight text-white">
            {kpis?.pending_approvals_count ?? 0}
          </div>
          <div className="text-[10px] font-mono text-street-amber">
            High-value refunds awaiting review
          </div>
        </div>
      </div>

      {/* Two Column Section: Recent Orders & Agent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Recent Orders Table */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono font-bold tracking-widest text-aether-400 uppercase">
              Recent Customer Orders
            </h2>
            <Link
              href="/admin/orders"
              className="text-xs font-mono text-white hover:text-street-amber transition-colors flex items-center gap-1"
            >
              All Orders ({kpis?.total_orders_count ?? 0}) →
            </Link>
          </div>

          <div className="rounded-2xl bg-aether-900/60 border border-aether-800 divide-y divide-aether-850 overflow-hidden shadow-xl">
            {recentOrders.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-aether-500">No orders logged.</div>
            ) : (
              recentOrders.map((ord) => (
                <div key={ord.id} className="p-4 flex items-center justify-between text-xs font-mono">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">{ord.order_number}</span>
                      <span className="text-[10px] text-aether-400">
                        {ord.carrier ? `${ord.carrier}` : "Carrier pending"}
                      </span>
                    </div>
                    <p className="text-[11px] text-aether-400 truncate max-w-xs">
                      {ord.items.map((it) => `${it.product_name} (${it.size})`).join(", ")}
                    </p>
                  </div>

                  <div className="text-right space-y-1">
                    <span className="font-bold text-white block">{formatINR(ord.total_amount_inr)}</span>
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                        ord.status === "Delivered"
                          ? "bg-street-emerald/20 text-street-emerald"
                          : ord.status === "In Transit"
                          ? "bg-street-cyan/20 text-street-cyan"
                          : ord.status === "Cancelled"
                          ? "bg-street-red/20 text-street-red"
                          : "bg-street-amber/20 text-street-amber"
                      }`}
                    >
                      {ord.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Multi-Agent Audit Log Sample */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-mono font-bold tracking-widest text-aether-400 uppercase">
              Supervisor Routing Trace
            </h2>
            <Link
              href="/admin/agent-logs"
              className="text-xs font-mono text-white hover:text-street-amber transition-colors flex items-center gap-1"
            >
              Full Audit Trail →
            </Link>
          </div>

          <div className="rounded-2xl bg-aether-900/60 border border-aether-800 p-4 space-y-3 font-mono shadow-xl">
            {recentLogs.length === 0 ? (
              <div className="py-6 text-center text-xs text-aether-500">No agent actions recorded.</div>
            ) : (
              recentLogs.map((log) => (
                <div key={log.id} className="p-3 rounded-xl bg-aether-950 border border-aether-850 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-aether-900 border border-aether-700 text-street-cyan">
                      {log.routed_agent.replace("Agent", "")}
                    </span>
                    <span className="text-[10px] text-aether-500">
                      {new Date(log.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>

                  <p className="text-white truncate">
                    <span className="text-aether-500">User:</span> "{log.user_message}"
                  </p>

                  {log.tool_called && (
                    <div className="text-[11px] text-street-amber truncate">
                      ↳ <span className="font-semibold">{log.tool_called}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
