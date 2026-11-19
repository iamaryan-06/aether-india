"use client";

import { useEffect, useState } from "react";
import { AgentActionLog } from "@/types";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { ScrollText, Bot, Search, RefreshCw, ChevronDown, ChevronUp, Code2 } from "lucide-react";

const AGENT_FILTERS = [
  "All",
  "CustomerSupportAgent",
  "OrderAndInventoryAgent",
  "RefundAndPaymentAgent",
  "NotificationAndEscalationAgent",
];

export default function AdminAgentLogsPage() {
  const [logs, setLogs] = useState<AgentActionLog[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);

  const { user, loginAsDemoAdmin } = useAuthStore();

  const loadLogs = async () => {
    setIsLoading(true);
    try {
      if (!user || user.role !== "admin") {
        await loginAsDemoAdmin();
      }
      const data = await api.getAdminAgentLogs(
        selectedAgent === "All" ? undefined : selectedAgent,
        50
      );
      setLogs(data);
    } catch (err) {
      console.error("Failed to load agent logs", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [user, selectedAgent]);

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case "CustomerSupportAgent":
        return "bg-street-purple/20 text-street-purple border-street-purple/40";
      case "OrderAndInventoryAgent":
        return "bg-street-emerald/20 text-street-emerald border-street-emerald/40";
      case "RefundAndPaymentAgent":
        return "bg-street-cyan/20 text-street-cyan border-street-cyan/40";
      case "NotificationAndEscalationAgent":
        return "bg-street-amber/20 text-street-amber border-street-amber/40";
      default:
        return "bg-aether-800 text-aether-300 border-aether-700";
    }
  };

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      log.user_message.toLowerCase().includes(query) ||
      (log.tool_called && log.tool_called.toLowerCase().includes(query)) ||
      log.session_id.toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black font-mono tracking-tight text-white uppercase flex items-center gap-2">
            <ScrollText className="w-6 h-6 text-street-amber" />
            Multi-Agent Audit Trail &amp; Routing Logs
          </h1>
          <p className="text-xs font-mono text-aether-400 mt-1">
            Immutable SQLite records of supervisor decisions, tool inputs, and RAG vector outputs.
          </p>
        </div>

        <button
          onClick={loadLogs}
          className="px-3.5 py-2 rounded-xl bg-aether-900 border border-aether-800 hover:border-aether-600 text-xs font-mono text-white transition-colors flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Logs
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Agent Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 text-xs font-mono">
          {AGENT_FILTERS.map((ag) => (
            <button
              key={ag}
              onClick={() => setSelectedAgent(ag)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                selectedAgent === ag
                  ? "bg-white text-black font-bold shadow"
                  : "bg-aether-900 border border-aether-800 text-aether-400 hover:text-white"
              }`}
            >
              {ag === "All" ? "All Agents" : ag.replace("Agent", "")}
            </button>
          ))}
        </div>

        {/* Query Search */}
        <div className="w-full md:w-64">
          <input
            type="text"
            placeholder="Search query or tool..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-aether-900 border border-aether-800 focus:border-white rounded-xl px-3.5 py-2 text-xs font-mono text-white placeholder-aether-500 focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Logs Table */}
      <div className="rounded-2xl bg-aether-900/60 border border-aether-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-aether-950 border-b border-aether-850 text-[10px] uppercase text-aether-500 tracking-wider">
              <tr>
                <th className="p-4">Timestamp &amp; Session</th>
                <th className="p-4">Customer Query</th>
                <th className="p-4">Supervisor Routed Agent</th>
                <th className="p-4">Tool Executed</th>
                <th className="p-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-aether-850">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-aether-500">
                    Loading agent audit logs...
                  </td>
                </tr>
              ) : filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-aether-500">
                    No action logs match the criteria.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const isExpanded = expandedLogId === log.id;

                  return (
                    <>
                      <tr key={log.id} className="hover:bg-aether-850/40 transition-colors">
                        {/* Timestamp & Session */}
                        <td className="p-4 space-y-1">
                          <span className="text-white block font-semibold">
                            {new Date(log.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })}
                          </span>
                          <span className="text-[10px] text-aether-500 truncate block max-w-[120px]">
                            {log.session_id}
                          </span>
                        </td>

                        {/* Customer Query */}
                        <td className="p-4 max-w-xs">
                          <p className="text-white font-medium truncate">"{log.user_message}"</p>
                          {log.user_id && (
                            <span className="text-[10px] text-aether-500">User ID: {log.user_id}</span>
                          )}
                        </td>

                        {/* Routed Agent */}
                        <td className="p-4">
                          <span
                            className={`inline-block px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider ${getAgentColor(
                              log.routed_agent
                            )}`}
                          >
                            {log.routed_agent.replace("Agent", "")}
                          </span>
                        </td>

                        {/* Tool Executed */}
                        <td className="p-4">
                          {log.tool_called ? (
                            <span className="text-street-amber font-semibold block truncate max-w-xs">
                              ↳ {log.tool_called}
                            </span>
                          ) : (
                            <span className="text-aether-500 italic">Direct LLM Response</span>
                          )}
                        </td>

                        {/* Expand Button */}
                        <td className="p-4 text-right">
                          <button
                            onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                            className="p-1.5 rounded-lg hover:bg-aether-800 text-aether-400 hover:text-white transition-colors"
                            title="Inspect tool payload"
                          >
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4" />
                            ) : (
                              <ChevronDown className="w-4 h-4" />
                            )}
                          </button>
                        </td>
                      </tr>

                      {/* Expanded JSON Inspector Row */}
                      {isExpanded && (
                        <tr className="bg-aether-950/80 border-y border-aether-850">
                          <td colSpan={5} className="p-4 space-y-3 font-mono text-[11px]">
                            <div className="flex items-center gap-1.5 text-street-cyan font-bold">
                              <Code2 className="w-4 h-4" />
                              <span>Step Inspection for Log #{log.id}</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {/* Tool Input */}
                              <div className="p-3 rounded-xl bg-aether-900 border border-aether-800 space-y-1">
                                <span className="text-[10px] uppercase text-aether-500 font-bold block">
                                  Tool Input:
                                </span>
                                <pre className="text-aether-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-48 text-[11px]">
                                  {log.tool_input || "No tool input arguments."}
                                </pre>
                              </div>

                              {/* Tool Output */}
                              <div className="p-3 rounded-xl bg-aether-900 border border-aether-800 space-y-1">
                                <span className="text-[10px] uppercase text-street-emerald font-bold block">
                                  Tool / RAG Output:
                                </span>
                                <pre className="text-aether-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-48 text-[11px]">
                                  {log.tool_output || "No tool output."}
                                </pre>
                              </div>
                            </div>

                            {/* Final AI Output */}
                            {log.final_response && (
                              <div className="p-3 rounded-xl bg-aether-900 border border-aether-800 space-y-1">
                                <span className="text-[10px] uppercase text-street-purple font-bold block">
                                  Final Agent Response to User:
                                </span>
                                <p className="text-aether-200 leading-relaxed">{log.final_response}</p>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
