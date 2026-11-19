"use client";

import { useState, useRef, useEffect } from "react";
import {
  X,
  Send,
  Sparkles,
  Bot,
  User as UserIcon,
  ShoppingBag,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  Package,
  ArrowRight,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { ChatMessage, ToolTraceItem } from "@/types";
import { api } from "@/lib/api";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";
import { formatINR } from "@/lib/utils";

interface AgentChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const QUICK_PROMPTS = [
  "What is your return policy & refund limit?",
  "Size chart for Boxy Hoodie with 42 in chest?",
  "Track my order AETH-1004",
  "Buy the Acid Wash Graphic Tee in size M using UPI",
  "Refund my Gore-Tex Jacket order AETH-1003",
  "Cancel order AETH-1001",
  "Exchange order AETH-1002 from size L to XL",
  "How to wash 480GSM heavyweight cotton?",
];

export default function AgentChatDrawer({ isOpen, onClose }: AgentChatDrawerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      role: "assistant",
      content:
        "Welcome to **AETHER INDIA**. I am your autonomous AI operations concierge powered by a **4-Agent LangGraph system**.\n\nI can check sizing measurements, recommend streetwear drops, track your BlueDart/Delhivery parcels, place orders directly in chat, or process automated returns up to ₹5,000.\n\nHow can I assist your streetwear wardrobe today?",
      timestamp: new Date().toISOString(),
      routed_agent: "CustomerSupportAgent",
      trace_badge: "Supervisor → CustomerSupportAgent",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const [isExpandedFull, setIsExpandedFull] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { addItem } = useCartStore();
  const { user } = useAuthStore();

  useEffect(() => {
    if (typeof window !== "undefined" && !sessionId) {
      setSessionId(`aether-session-${Math.random().toString(36).substring(2, 10)}`);
    }
  }, [sessionId]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!messageText) setInput("");
    setIsLoading(true);

    try {
      const data = await api.sendChatMessage(text, sessionId);

      // Parse structured payload if present in response
      let parsedProducts: any[] | undefined = undefined;
      let orderConfirmationCard: any | undefined = undefined;
      let escalationCard: any | undefined = undefined;

      // Extract JSON product cards or order results if embedded in response
      if (data.response.includes('"products":') && data.response.includes('"sku":')) {
        try {
          const match = data.response.match(/\{[\s\S]*"products"[\s\S]*\}/);
          if (match) {
            const parsed = JSON.parse(match[0]);
            parsedProducts = parsed.products;
          }
        } catch {}
      }

      // Check tool trace for create_new_order results
      const orderTool = data.tool_trace?.find((t: ToolTraceItem) => t.tool === "create_new_order");
      if (orderTool?.output_summary && orderTool.output_summary.includes("order_number")) {
        try {
          const outMatch = orderTool.output_summary.match(/AETH-\d{4}/);
          if (outMatch) {
            orderConfirmationCard = { order_number: outMatch[0] };
          }
        } catch {}
      }

      // Check tool trace for escalation
      const escalationTool = data.tool_trace?.find(
        (t: ToolTraceItem) => t.tool === "escalate_to_human_admin" || (t.tool === "process_refund_or_exchange" && t.output_summary?.includes("ESCALATED"))
      );
      if (escalationTool) {
        escalationCard = {
          title: "Escalated for Human Authorization",
          note: "Refund exceeds ₹5,000 auto-approval threshold. Ticket queued for Operations Head review.",
        };
      }

      const assistantMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
        routed_agent: data.routed_agent,
        trace_badge: data.trace_badge,
        tool_trace: data.tool_trace,
        productCards: parsedProducts,
        orderCard: orderConfirmationCard,
        escalationCard: escalationCard,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `I encountered an issue communicating with the multi-agent system: ${err.message}. Please verify the backend is running.`,
        timestamp: new Date().toISOString(),
        trace_badge: "System → Error Handler",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getAgentColor = (agent?: string) => {
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden pointer-events-none">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto transition-opacity" onClick={onClose} />

      <aside
        className={`pointer-events-auto absolute right-0 top-0 bottom-0 flex flex-col bg-aether-950/95 border-l border-aether-800 shadow-2xl transition-all duration-300 ease-out z-10 ${
          isExpandedFull ? "w-full md:w-4/5 lg:w-3/5" : "w-full sm:w-[540px]"
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-aether-800 flex items-center justify-between bg-aether-900/60 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-street-red/30 via-street-purple/30 to-street-cyan/30 border border-white/10">
              <Sparkles className="w-5 h-5 text-street-amber" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-mono font-bold tracking-tight text-white uppercase">AETHER Autonomous Agent</h2>
                <span className="w-2 h-2 rounded-full bg-street-emerald animate-pulse" />
              </div>
              <p className="text-[11px] font-mono text-aether-400">4-Agent LangGraph Supervisor Core</p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setIsExpandedFull(!isExpandedFull)}
              className="p-2 rounded-lg hover:bg-aether-800 text-aether-400 hover:text-white transition-colors"
              title={isExpandedFull ? "Standard size" : "Expand drawer"}
            >
              {isExpandedFull ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-aether-800 text-aether-400 hover:text-white transition-colors"
              title="Close chat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Multi-Agent Architecture Legend Banner */}
        <div className="px-4 py-2 bg-aether-900/40 border-b border-aether-850 flex items-center justify-between text-[10px] font-mono text-aether-400 overflow-x-auto gap-2">
          <span className="shrink-0 text-aether-500 font-semibold uppercase">Active Agents:</span>
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="px-1.5 py-0.5 rounded bg-street-purple/10 text-street-purple border border-street-purple/20">1: Support</span>
            <span className="px-1.5 py-0.5 rounded bg-street-emerald/10 text-street-emerald border border-street-emerald/20">2: Orders</span>
            <span className="px-1.5 py-0.5 rounded bg-street-cyan/10 text-street-cyan border border-street-cyan/20">3: Refunds</span>
            <span className="px-1.5 py-0.5 rounded bg-street-amber/10 text-street-amber border border-street-amber/20">4: HITL</span>
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
              {/* Message Bubble Container */}
              <div className="flex gap-2.5 max-w-[92%] sm:max-w-[85%]">
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 rounded-lg bg-aether-900 border border-aether-800 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-street-cyan" />
                  </div>
                )}

                <div className="flex flex-col gap-1.5">
                  {/* MULTI-AGENT EXECUTION TRACE BADGE */}
                  {msg.role === "assistant" && msg.trace_badge && (
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                      <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-aether-900 border border-aether-700 text-aether-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-street-cyan" />
                        <span>{msg.trace_badge}</span>
                      </div>

                      {msg.routed_agent && (
                        <span className={`px-2 py-0.5 rounded-full border text-[9px] font-semibold uppercase tracking-wider ${getAgentColor(msg.routed_agent)}`}>
                          {msg.routed_agent.replace("Agent", "")}
                        </span>
                      )}

                      {/* Expandable tool trace toggler */}
                      {msg.tool_trace && msg.tool_trace.length > 0 && (
                        <button
                          onClick={() => setExpandedTraceId(expandedTraceId === msg.id ? null : msg.id)}
                          className="px-1.5 py-0.5 rounded bg-aether-850 hover:bg-aether-800 text-aether-400 hover:text-white transition-colors flex items-center gap-0.5"
                        >
                          <span>{msg.tool_trace.length} tool(s)</span>
                          {expandedTraceId === msg.id ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Expandable Tool Trace Details */}
                  {expandedTraceId === msg.id && msg.tool_trace && (
                    <div className="p-2.5 rounded-lg bg-aether-950 border border-aether-800 font-mono text-[11px] space-y-2 text-aether-300">
                      <div className="text-[10px] uppercase tracking-wider text-aether-500 font-semibold border-b border-aether-850 pb-1">
                        Execution Step Inspection
                      </div>
                      {msg.tool_trace.map((step, idx) => (
                        <div key={idx} className="space-y-0.5">
                          <div className="flex items-center gap-1.5 text-street-amber font-semibold">
                            <span>↳</span>
                            <span>{step.tool}</span>
                            <span className="text-[9px] text-aether-500">({step.agent})</span>
                          </div>
                          {step.input_summary && (
                            <div className="text-[10px] text-aether-400 pl-4 truncate">
                              <span className="text-aether-500">in:</span> {step.input_summary}
                            </div>
                          )}
                          {step.output_summary && (
                            <div className="text-[10px] text-street-emerald pl-4 truncate">
                              <span className="text-aether-500">out:</span> {step.output_summary}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Message Content Bubble */}
                  <div
                    className={`p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap ${
                      msg.role === "user"
                        ? "bg-white text-black font-medium rounded-tr-none shadow-md"
                        : "bg-aether-900 border border-aether-800 text-aether-100 rounded-tl-none shadow-xl"
                    }`}
                  >
                    {msg.content}
                  </div>

                  {/* Interactive Cards: Order Confirmation */}
                  {msg.orderCard && (
                    <div className="mt-2 p-3.5 rounded-xl bg-street-emerald/10 border border-street-emerald/30 text-white font-mono space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-street-emerald flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4" /> Order Created via AI
                        </span>
                        <span className="px-2 py-0.5 text-[10px] bg-street-emerald/20 text-street-emerald rounded font-bold">
                          {msg.orderCard.order_number}
                        </span>
                      </div>
                      <p className="text-[11px] text-aether-300">
                        Stock deducted and order confirmed. View live tracking and carrier status in your orders portal.
                      </p>
                      <a
                        href="/orders"
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-street-emerald hover:underline"
                      >
                        Open My Orders <ArrowRight className="w-3 h-3" />
                      </a>
                    </div>
                  )}

                  {/* Interactive Cards: Escalation Flag */}
                  {msg.escalationCard && (
                    <div className="mt-2 p-3.5 rounded-xl bg-street-amber/10 border border-street-amber/30 text-white font-mono space-y-1.5">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-street-amber">
                        <ShieldAlert className="w-4 h-4" />
                        <span>{msg.escalationCard.title}</span>
                      </div>
                      <p className="text-[11px] text-aether-300">{msg.escalationCard.note}</p>
                    </div>
                  )}

                  <span className="text-[9px] font-mono text-aether-600 px-1">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>

                {msg.role === "user" && (
                  <div className="w-7 h-7 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center shrink-0 mt-1">
                    <UserIcon className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isLoading && (
            <div className="flex items-center gap-2 text-aether-400 font-mono text-xs p-2">
              <div className="w-7 h-7 rounded-lg bg-aether-900 border border-aether-800 flex items-center justify-center shrink-0 animate-pulse">
                <Bot className="w-4 h-4 text-street-cyan" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="inline-block w-2 h-2 rounded-full bg-street-cyan animate-bounce" />
                <span className="inline-block w-2 h-2 rounded-full bg-street-purple animate-bounce [animation-delay:0.2s]" />
                <span className="inline-block w-2 h-2 rounded-full bg-street-amber animate-bounce [animation-delay:0.4s]" />
                <span className="text-[11px] text-aether-400 ml-1">Supervisor routing query...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="p-3 border-t border-aether-850 bg-aether-950/60 overflow-x-auto no-scrollbar">
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                disabled={isLoading}
                className="px-2.5 py-1 rounded-full bg-aether-900 border border-aether-800 hover:border-aether-600 text-aether-300 hover:text-white text-[11px] font-mono transition-colors disabled:opacity-50 shrink-0"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-aether-800 bg-aether-900/80 backdrop-blur-xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything: sizing, stock, order status, refund..."
              disabled={isLoading}
              className="flex-1 bg-aether-950 border border-aether-800 focus:border-white rounded-xl px-4 py-2.5 text-xs sm:text-sm text-white placeholder-aether-500 focus:outline-none transition-colors font-mono"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-2.5 rounded-xl bg-white hover:bg-aether-200 text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="mt-2 text-center text-[10px] font-mono text-aether-500">
            Automated LangGraph Router • Refunds ≤ ₹5,000 Auto-Processed • &gt; ₹5,000 Escalated
          </div>
        </div>
      </aside>
    </div>
  );
}
