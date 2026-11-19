"""
agent.py — AETHER INDIA LangGraph Multi-Agent System.

Architecture: Supervisor Router Pattern
────────────────────────────────────────────────────────────────────
START
  │
  ▼
supervisor_node        ← LLM reads conversation, decides which agent to run
  │
  ├── CustomerSupportAgent        (RAG + product search)
  ├── OrderAndInventoryAgent      (orders, tracking, cancellation)
  ├── RefundAndPaymentAgent       (refunds, exchanges, ₹5k threshold)
  └── NotificationAndEscalationAgent (notifications, HITL tickets)
  │
  ▼ (each agent returns to supervisor after its turn)
  │
  └── END (when supervisor decides task is complete)
────────────────────────────────────────────────────────────────────

LLM providers (configurable via .env):
  LLM_PROVIDER=gemini  → ChatGoogleGenerativeAI  (gemini-2.5-flash)
  LLM_PROVIDER=groq    → ChatGroq                (llama-3.3-70b-versatile)

Handoff:
  Agent 2 / 3 tools return {"handoff_to_agent4": true} in their JSON output.
  The supervisor reads this signal and routes to NotificationAndEscalationAgent
  before ending the conversation turn.

Public API:
  run_agent(message, user_id, session_id) -> AetherAgentResult
"""
from __future__ import annotations

import io
import json
import os
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal, Optional

from dotenv import load_dotenv

load_dotenv()

# ── Path bootstrap ─────────────────────────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# ── LangChain / LangGraph ─────────────────────────────────────────────────────
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, create_react_agent

# ── Project imports ────────────────────────────────────────────────────────────
from agents.tools import (
    AGENT1_TOOLS,
    AGENT2_TOOLS,
    AGENT3_TOOLS,
    AGENT4_TOOLS,
    send_customer_notification,
    escalate_to_human_admin,
)
from db.database import SessionLocal
from db.models import AgentActionLog


# ─────────────────────────────────────────────────────────────────────────────
# 1.  LLM Factory
# ─────────────────────────────────────────────────────────────────────────────

def _make_gemini_llm(temperature: float):
    """Build and return a Gemini LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key or api_key.startswith("AIza..."):
        raise EnvironmentError("GOOGLE_API_KEY is not set or is still the placeholder.")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        convert_system_message_to_human=False,
    )


def _make_groq_llm(temperature: float):
    """Build and return a Groq LLM instance."""
    from langchain_groq import ChatGroq
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key.startswith("gsk_..."):
        raise EnvironmentError("GROQ_API_KEY is not set or is still the placeholder.")
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(
        model=model_name,
        groq_api_key=api_key,
        temperature=temperature,
    )


# Ordered fallback chain: primary provider is tried first, then the rest in order.
_PROVIDER_CHAIN = ["gemini", "groq"]
_PROVIDER_FACTORIES = {
    "gemini": _make_gemini_llm,
    "groq": _make_groq_llm,
}


def get_llm(temperature: float = 0.1):
    """
    Return a configured LangChain chat model with runtime automatic fallback.

    Provider priority:
        1. Primary provider from LLM_PROVIDER env var (default: gemini)
        2. Fallback provider(s) attached via .with_fallbacks() (e.g. groq)

    If the primary provider hits a 429 (rate-limit / quota exhausted) or network error
    at runtime, LangChain automatically switches to the fallback provider without failing.
    """
    primary = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    ordered = [primary] + [p for p in _PROVIDER_CHAIN if p != primary]

    instances = []
    for provider in ordered:
        factory = _PROVIDER_FACTORIES.get(provider)
        if not factory:
            continue
        try:
            model = factory(temperature)
            instances.append((provider, model))
        except Exception as exc:
            print(f"[LLM] Notice: Provider '{provider}' not available: {exc}")

    if not instances:
        raise RuntimeError("No LLM providers available. Check API keys in backend/.env")

    primary_name, primary_llm = instances[0]
    fallbacks = [m for _, m in instances[1:]]

    if fallbacks:
        print(f"[LLM] Configured '{primary_name}' with fallback chain: {[name for name, _ in instances[1:]]}")
        return primary_llm.with_fallbacks(fallbacks)
    else:
        print(f"[LLM] Running with single provider '{primary_name}'")
        return primary_llm


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Agent State
# ─────────────────────────────────────────────────────────────────────────────

from typing import TypedDict


class AetherAgentState(TypedDict):
    """
    Shared state that flows through every node in the LangGraph StateGraph.

    messages       — full conversation history (add_messages reducer de-duplicates)
    session_id     — UUID for this browser session (used in AgentActionLog)
    user_id        — authenticated customer's DB id (None for unauthenticated)
    next_agent     — routing decision from supervisor ("FINISH" → END)
    routed_agent   — name of the last agent that executed (for the UI badge)
    tool_trace     — list of {agent, tool, input_summary, output_summary}
    iteration      — guard against infinite supervisor loops
    """
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    user_id: Optional[int]
    next_agent: str
    routed_agent: Optional[str]
    tool_trace: list[dict]
    iteration: int


# ─────────────────────────────────────────────────────────────────────────────
# 3.  System Prompts
# ─────────────────────────────────────────────────────────────────────────────

SUPERVISOR_SYSTEM_PROMPT = """\
You are the AETHER INDIA Supervisor AI — the central router for a 4-agent \
luxury streetwear e-commerce assistant system.

Your ONLY job is to decide which specialized agent should handle the customer's \
current request. You do NOT answer questions yourself — you route them.

## Available Agents

1. **CustomerSupportAgent**
   Handles: Return & refund policy questions, size & fit advice, \
fabric care instructions, shipping SLA queries, product recommendations, \
styling suggestions, outfit building.
   Trigger keywords: size, fit, return policy, shipping time, fabric, wash, \
GSM, recommend, suggest, outfit, style, what size, measure.

2. **OrderAndInventoryAgent**
   Handles: Placing new orders from chat, checking order status & tracking, \
stock availability, cart operations, cancelling orders, modifying shipping addresses.
   Trigger keywords: order, buy, purchase, track, where is my, cancel, \
change address, add to cart, stock, available, place order, create order.

3. **RefundAndPaymentAgent**
   Handles: Refund requests, size exchanges, payment verification (UPI/Card/COD), \
RMA label generation. Enforces the ₹5,000 auto-refund threshold — amounts \
above ₹5,000 are automatically escalated to Admin.
   Trigger keywords: refund, exchange, return item, payment, transaction, \
UPI, Razorpay, exchange size, RMA, money back, paid, failed payment.

4. **NotificationAndEscalationAgent**
   Handles: Sending in-app notifications, creating Human-in-the-Loop (HITL) \
admin approval tickets, escalating policy disputes to a human admin.
   Trigger keywords: notify, escalate, talk to human, human agent, dispute, \
I disagree, policy exception, supervisor, manager.
   ALSO called automatically after Agent 2 or Agent 3 completes an action \
that requires a customer notification (order created, refund processed, \
exchange approved, cancellation confirmed).

## Routing Rules

- After Agent 2 (OrderAndInventoryAgent) successfully creates, cancels, or \
modifies an order — ALWAYS route to NotificationAndEscalationAgent next \
(look for "requires_notification": true in the last tool result).
- After Agent 3 (RefundAndPaymentAgent) approves a refund or exchange, OR \
escalates to admin — ALWAYS route to NotificationAndEscalationAgent next.
- After NotificationAndEscalationAgent completes — route to FINISH.
- If the task is fully complete (customer question answered, notification sent) \
— route to FINISH.
- Never route to the same agent twice in a row unless the agent explicitly \
needs to call another tool.
- Maximum 8 routing steps per conversation turn to prevent loops.

## Output Format

Respond with ONLY a raw JSON object — no markdown, no explanation:
{"next_agent": "<agent_name_or_FINISH>", "reason": "<one-line reason>"}

Valid values for next_agent:
  "CustomerSupportAgent"
  "OrderAndInventoryAgent"
  "RefundAndPaymentAgent"
  "NotificationAndEscalationAgent"
  "FINISH"
"""

AGENT1_SYSTEM_PROMPT = """\
You are the AETHER INDIA Customer Support Agent — an expert on the brand's \
products, policies, sizing, and fabric care.

Your tools:
1. query_brand_knowledge_rag — ALWAYS call this first for ANY policy, size, \
shipping, or care question. It returns excerpts from our official policy documents.
2. search_and_style_products — Use this to recommend products, build outfits, \
or check what's available in a size/category/budget.

## Behaviour Guidelines
- For sizing questions, ALWAYS include the exact measurement chart from the RAG results.
- For return/refund policy questions, mention the ₹5,000 auto-refund threshold clearly.
- For product recommendations, return structured product cards (the JSON from the tool) \
and add a short styling tip for each.
- Be warm, knowledgeable, and on-brand — AETHER is luxury streetwear, not fast fashion.
- Always answer in the same language the customer writes in (default: English).
- Prices are always in Indian Rupees (₹ / INR).
"""

AGENT2_SYSTEM_PROMPT = """\
You are the AETHER INDIA Order & Inventory Agent — responsible for order creation, \
live tracking, cancellations, and stock management.

Your tools:
1. create_new_order — Creates a real order in the database. ALWAYS confirm the \
   product SKU, size, and shipping address before calling this tool.
2. check_inventory_and_add_to_cart — Validates stock before cart-add (UI flow).
3. check_order_status — Fetches live status, carrier, tracking number, and ETA.
4. cancel_or_modify_order — Cancels or modifies an order. STRICT RULES APPLY:
   - Only cancellable if status is Processing or Packed.
   - In Transit or Delivered → refuse, suggest return/refund.
   - On cancellation, stock is automatically restored.

## Behaviour Guidelines
- Before creating an order, confirm: SKU, size, quantity, address, payment method.
- When displaying an order confirmation, always show the AETH-XXXX order number, \
  carrier, estimated delivery, and payment status prominently.
- Prices and totals in ₹ (INR) only.
- If a cancellation is blocked, be empathetic and suggest the return process.
- After completing any order action, your response MUST signal \
  "requires_notification: true" so the supervisor routes to Agent 4.
"""

AGENT3_SYSTEM_PROMPT = """\
You are the AETHER INDIA Refund & Payment Agent — responsible for processing \
refunds, size exchanges, and payment verification.

Your tools:
1. check_payment_and_refund_status — Call this FIRST to verify payment, check \
   the 14-day return window, and confirm the refund amount.
2. process_refund_or_exchange — Processes the refund or exchange after verification.

## ₹5,000 Refund Threshold (CRITICAL RULE)
- Refund amount <= ₹5,000 AND order Delivered AND within 14 days:
    → AUTO-APPROVE immediately. Update status to Refunded. No admin needed.
- Refund amount > ₹5,000:
    → ESCALATE. Create a PENDING_ADMIN ticket. Customer is told to wait 24-48h.
    → DO NOT auto-approve regardless of circumstances.

## Exchange Flow
1. Verify 14-day window is not expired.
2. Check target size is in stock.
3. Decrement stock, generate RMA label, update order to Exchanged.
4. Free reverse pickup for exchanges (no ₹99 fee).

## Behaviour Guidelines
- Always check_payment_and_refund_status before calling process_refund_or_exchange.
- After refund/exchange, the supervisor will route to Agent 4 for notification — \
  your final response should summarise what was done clearly.
- Mention refund timelines: 3-5 days UPI, 5-7 days Card, 5-7 days COD via NEFT.
- Be empathetic — customers contacting about refunds are often frustrated.
"""

AGENT4_SYSTEM_PROMPT = """\
You are the AETHER INDIA Notification & Escalation Agent — responsible for \
sending in-app notifications to customers and creating HITL admin tickets.

Your tools:
1. send_customer_notification — Writes a Notification record to the database \
   so it appears in the customer's notification bell. Call this for:
   ORDER_CONFIRMED, REFUND_PROCESSED, EXCHANGE_APPROVED, CANCELLATION_CONFIRMED, ORDER_SHIPPED
2. escalate_to_human_admin — Creates a PENDING_ADMIN ApprovalRequest ticket \
   AND automatically notifies the customer. Call this for:
   HIGH_VALUE_REFUND (refund > ₹5,000), POLICY_EXCEPTION

## When you are called with context from Agent 2 or 3
- Parse the last tool result to extract: user_id, notification_type, notification_title, \
  notification_message, and whether escalation is needed.
- For handoff from Agent 3 with agent4_task="ESCALATE": call escalate_to_human_admin.
- For handoff from Agent 2 or 3 with agent4_task="SEND_NOTIFICATION": call send_customer_notification.
- If both are needed: call escalate_to_human_admin (which sends the notification automatically).

## Behaviour Guidelines
- After sending the notification, confirm to the customer: \
  "A notification has been sent to your account."
- Keep your response concise — the main action was done by Agent 2 or 3.
- If called directly by the customer asking to "talk to a human" or "escalate", \
  call escalate_to_human_admin with action_type="POLICY_EXCEPTION".
"""


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Agent Node Builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_agent_node(agent_name: str, tools: list[BaseTool], system_prompt: str):
    """
    Build a LangGraph node function for a specialized agent using create_react_agent.

    The agent receives the full conversation history, executes its ReAct loop
    (call LLM → call tools → call LLM → … → final answer), and returns updated
    state with messages, routed_agent, and tool_trace.
    """
    llm = get_llm(temperature=0.1)

    # create_react_agent returns a compiled subgraph that handles the ReAct loop
    agent_graph = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SystemMessage(content=system_prompt),
    )

    def node_fn(state: AetherAgentState) -> dict:
        """Execute this agent's ReAct loop and return updated state."""
        try:
            result = agent_graph.invoke(
                {"messages": state["messages"]},
                config={"recursion_limit": 10},
            )
        except Exception as exc:
            error_text = f"[{agent_name}] encountered an error: {exc}"
            return {
                "messages": [AIMessage(content=error_text)],
                "routed_agent": agent_name,
                "tool_trace": state.get("tool_trace", [])
                + [{"agent": agent_name, "error": str(exc)}],
                "next_agent": "FINISH",
            }

        new_messages: list[BaseMessage] = result.get("messages", [])

        # Build tool trace from the new messages (ToolMessage entries)
        trace_entries = list(state.get("tool_trace", []))
        for msg in new_messages:
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace_entries.append({
                        "agent": agent_name,
                        "tool": tc.get("name", "unknown"),
                        "input_summary": _summarise_tool_input(tc.get("args", {})),
                        "output_summary": None,  # filled below
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            elif isinstance(msg, ToolMessage):
                # Attach output to the most recent trace entry missing it
                for entry in reversed(trace_entries):
                    if entry.get("agent") == agent_name and entry.get("output_summary") is None:
                        entry["output_summary"] = _summarise_tool_output(msg.content)
                        break

        return {
            "messages": new_messages,
            "routed_agent": agent_name,
            "tool_trace": trace_entries,
            "iteration": state.get("iteration", 0) + 1,
        }

    node_fn.__name__ = agent_name
    return node_fn


def _summarise_tool_input(args: dict) -> str:
    """Return a compact 1-line summary of tool arguments for the trace badge."""
    try:
        text = json.dumps(args, ensure_ascii=False)
        return text[:120] + "…" if len(text) > 120 else text
    except Exception:
        return str(args)[:120]


def _summarise_tool_output(content: Any) -> str:
    """Return a compact 1-line summary of tool output for the trace badge."""
    try:
        text = str(content)
        if len(text) > 150:
            # Try to extract a meaningful summary from JSON
            try:
                obj = json.loads(text)
                if isinstance(obj, dict):
                    for key in ("message", "order_number", "error", "result", "success"):
                        if key in obj:
                            return f"{key}: {str(obj[key])[:120]}"
            except Exception:
                pass
            return text[:150] + "…"
        return text
    except Exception:
        return str(content)[:150]


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Supervisor Node
# ─────────────────────────────────────────────────────────────────────────────

_VALID_AGENTS = {
    "CustomerSupportAgent",
    "OrderAndInventoryAgent",
    "RefundAndPaymentAgent",
    "NotificationAndEscalationAgent",
    "FINISH",
}


def _supervisor_node(state: AetherAgentState) -> dict:
    """
    Call the supervisor LLM to decide which agent handles the next step.

    The LLM reads the full conversation (including any tool results from
    previous agents) and outputs a JSON routing decision.

    Returns:
        {"next_agent": "<agent_name_or_FINISH>"}
    """
    # Safety: prevent runaway loops
    iteration = state.get("iteration", 0)
    if iteration >= 8:
        return {"next_agent": "FINISH", "iteration": iteration}

    llm = get_llm(temperature=0.0)

    # Build a condensed conversation string for the supervisor to analyse
    conversation_summary = _build_conversation_summary(state["messages"])

    supervisor_human_msg = HumanMessage(
        content=(
            f"Current conversation:\n{conversation_summary}\n\n"
            f"Routing step #{iteration + 1}. "
            f"Which agent should run next? Reply with ONLY the JSON object."
        )
    )

    supervisor_messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        supervisor_human_msg,
    ]

    try:
        response = llm.invoke(supervisor_messages)
        raw = response.content if hasattr(response, "content") else str(response)
        routing = _parse_routing_decision(raw)
    except Exception as exc:
        # Fallback: try to infer from conversation if LLM call fails
        routing = _fallback_routing(state["messages"], iteration)

    next_agent = routing.get("next_agent", "FINISH")
    if next_agent not in _VALID_AGENTS:
        next_agent = "FINISH"

    return {
        "next_agent": next_agent,
        "iteration": iteration + 1,
    }


def _build_conversation_summary(messages: list[BaseMessage]) -> str:
    """
    Condense the last N messages into a text summary for the supervisor prompt.
    """
    # Use the last 10 messages to stay within context limits
    recent = messages[-10:]
    parts = []
    for msg in recent:
        if isinstance(msg, HumanMessage):
            parts.append(f"CUSTOMER: {str(msg.content)[:300]}")
        elif isinstance(msg, AIMessage):
            content = str(msg.content)[:300]
            if msg.tool_calls:
                tools_called = [tc.get("name") for tc in msg.tool_calls]
                parts.append(f"AI (called tools: {tools_called}): {content}")
            else:
                parts.append(f"AI: {content}")
        elif isinstance(msg, ToolMessage):
            parts.append(f"TOOL RESULT: {str(msg.content)[:300]}")
        elif isinstance(msg, SystemMessage):
            pass  # Skip system messages from summary
    return "\n".join(parts) if parts else "No messages yet."


def _parse_routing_decision(raw: str) -> dict:
    """
    Extract the routing JSON from the supervisor LLM's response.
    Handles markdown code fences and stray text around the JSON.
    """
    text = raw.strip()

    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Find JSON object in the text
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # Last resort: keyword scan
    for agent in _VALID_AGENTS:
        if agent in text:
            return {"next_agent": agent, "reason": "keyword match"}

    return {"next_agent": "FINISH", "reason": "parse fallback"}


def _fallback_routing(messages: list[BaseMessage], iteration: int) -> dict:
    """
    Keyword-based routing fallback when the supervisor LLM call fails.
    Only used on the FIRST turn (iteration == 0). Otherwise FINISH.
    """
    if iteration > 0:
        return {"next_agent": "FINISH"}

    # Look at the last human message
    last_human = next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)),
        None,
    )
    if not last_human:
        return {"next_agent": "CustomerSupportAgent"}

    text = str(last_human.content).lower()

    refund_kw = ("refund", "exchange", "return item", "money back", "rma", "exchange size")
    order_kw = ("order", "buy", "purchase", "track", "cancel", "where is my", "add to cart")
    notif_kw = ("escalate", "human", "manager", "dispute", "policy exception")

    if any(kw in text for kw in refund_kw):
        return {"next_agent": "RefundAndPaymentAgent"}
    if any(kw in text for kw in order_kw):
        return {"next_agent": "OrderAndInventoryAgent"}
    if any(kw in text for kw in notif_kw):
        return {"next_agent": "NotificationAndEscalationAgent"}
    return {"next_agent": "CustomerSupportAgent"}


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Routing function (conditional edges)
# ─────────────────────────────────────────────────────────────────────────────

def _route_from_supervisor(state: AetherAgentState) -> str:
    """Return the next node name based on supervisor's routing decision."""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH" or next_agent not in _VALID_AGENTS:
        return END
    return next_agent


# ─────────────────────────────────────────────────────────────────────────────
# 7.  Graph Construction
# ─────────────────────────────────────────────────────────────────────────────

def _build_graph() -> Any:
    """
    Construct and compile the AETHER INDIA LangGraph StateGraph.

    Topology:
        START → supervisor → [agent nodes] → supervisor → … → END
    """
    workflow = StateGraph(AetherAgentState)

    # ── Nodes ─────────────────────────────────────────────────────────────────
    workflow.add_node("supervisor", _supervisor_node)

    workflow.add_node(
        "CustomerSupportAgent",
        _build_agent_node("CustomerSupportAgent", AGENT1_TOOLS, AGENT1_SYSTEM_PROMPT),
    )
    workflow.add_node(
        "OrderAndInventoryAgent",
        _build_agent_node("OrderAndInventoryAgent", AGENT2_TOOLS, AGENT2_SYSTEM_PROMPT),
    )
    workflow.add_node(
        "RefundAndPaymentAgent",
        _build_agent_node("RefundAndPaymentAgent", AGENT3_TOOLS, AGENT3_SYSTEM_PROMPT),
    )
    workflow.add_node(
        "NotificationAndEscalationAgent",
        _build_agent_node("NotificationAndEscalationAgent", AGENT4_TOOLS, AGENT4_SYSTEM_PROMPT),
    )

    # ── Edges ──────────────────────────────────────────────────────────────────
    # Entry point
    workflow.add_edge(START, "supervisor")

    # Supervisor routes to one of the 4 agents or END
    workflow.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {
            "CustomerSupportAgent": "CustomerSupportAgent",
            "OrderAndInventoryAgent": "OrderAndInventoryAgent",
            "RefundAndPaymentAgent": "RefundAndPaymentAgent",
            "NotificationAndEscalationAgent": "NotificationAndEscalationAgent",
            END: END,
        },
    )

    # Each agent returns to supervisor after completing its turn
    for agent_name in (
        "CustomerSupportAgent",
        "OrderAndInventoryAgent",
        "RefundAndPaymentAgent",
        "NotificationAndEscalationAgent",
    ):
        workflow.add_edge(agent_name, "supervisor")

    return workflow.compile()


# ── Compile once at module load ───────────────────────────────────────────────
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ─────────────────────────────────────────────────────────────────────────────
# 8.  Agent Action Logging
# ─────────────────────────────────────────────────────────────────────────────

def _log_agent_actions(
    session_id: str,
    user_id: Optional[int],
    user_message: str,
    tool_trace: list[dict],
    final_response: str,
) -> None:
    """
    Write one AgentActionLog row per tool call to the SQLite audit table.
    Errors are swallowed so logging never breaks the main response flow.
    """
    db = SessionLocal()
    try:
        for entry in tool_trace:
            log = AgentActionLog(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message[:1000],
                routed_agent=entry.get("agent", "unknown"),
                tool_called=entry.get("tool"),
                tool_input=entry.get("input_summary"),
                tool_output=entry.get("output_summary"),
                final_response=final_response[:2000] if final_response else None,
            )
            db.add(log)

        # If no tool was called (pure LLM response), log a single entry
        if not tool_trace:
            log = AgentActionLog(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message[:1000],
                routed_agent="CustomerSupportAgent",
                tool_called=None,
                tool_input=None,
                tool_output=None,
                final_response=final_response[:2000] if final_response else None,
            )
            db.add(log)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# 9.  Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

class AetherAgentResult:
    """
    Structured result returned by run_agent().

    Attributes:
        response       — the final AI message content (for the chat UI)
        routed_agent   — last agent that produced the answer
        tool_trace     — list of tool call dicts for the Execution Trace Badge
        all_messages   — full message list (for multi-turn conversation context)
        session_id     — session UUID
        error          — error string if run failed, else None
    """
    __slots__ = (
        "response", "routed_agent", "tool_trace",
        "all_messages", "session_id", "error",
    )

    def __init__(
        self,
        response: str,
        routed_agent: Optional[str],
        tool_trace: list[dict],
        all_messages: list[BaseMessage],
        session_id: str,
        error: Optional[str] = None,
    ) -> None:
        self.response = response
        self.routed_agent = routed_agent
        self.tool_trace = tool_trace
        self.all_messages = all_messages
        self.session_id = session_id
        self.error = error

    def to_dict(self) -> dict:
        """Serialise to a plain dict (used by the FastAPI /api/chat endpoint)."""
        # Build the execution trace badge string:
        # "Supervisor → CustomerSupportAgent → query_brand_knowledge_rag"
        if self.tool_trace:
            steps = ["Supervisor"]
            seen_agents = []
            for entry in self.tool_trace:
                agent = entry.get("agent", "")
                if agent and agent not in seen_agents:
                    seen_agents.append(agent)
                    steps.append(agent)
                tool = entry.get("tool")
                if tool and (not steps or steps[-1] != tool):
                    steps.append(tool)
            trace_badge = " → ".join(steps)
        elif self.routed_agent:
            trace_badge = f"Supervisor → {self.routed_agent}"
        else:
            trace_badge = "Supervisor"

        return {
            "response": self.response,
            "routed_agent": self.routed_agent,
            "trace_badge": trace_badge,
            "tool_trace": self.tool_trace,
            "session_id": self.session_id,
            "error": self.error,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 10.  Public Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def run_agent(
    message: str,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    conversation_history: Optional[list[BaseMessage]] = None,
) -> AetherAgentResult:
    """
    Run the AETHER multi-agent system for a single user turn.

    Args:
        message:              The customer's latest message.
        user_id:              Authenticated customer's DB user ID (None = anonymous).
        session_id:           Browser session UUID. A new one is created if not provided.
        conversation_history: Previous messages for multi-turn context.
                              Pass the `all_messages` from the previous AetherAgentResult
                              to maintain conversation continuity.

    Returns:
        AetherAgentResult with the final response and full execution trace.
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    # Build the initial message list
    prior_messages: list[BaseMessage] = conversation_history or []
    new_human_message = HumanMessage(content=message)

    initial_state: AetherAgentState = {
        "messages": prior_messages + [new_human_message],
        "session_id": session_id,
        "user_id": user_id,
        "next_agent": "",
        "routed_agent": None,
        "tool_trace": [],
        "iteration": 0,
    }

    try:
        graph = _get_graph()
        final_state = graph.invoke(
            initial_state,
            config={"recursion_limit": 25},
        )
    except Exception as exc:
        tb = traceback.format_exc()
        error_msg = (
            f"I'm sorry, I encountered an issue processing your request. "
            f"Please try again. (Error: {type(exc).__name__})"
        )
        result = AetherAgentResult(
            response=error_msg,
            routed_agent=None,
            tool_trace=[],
            all_messages=prior_messages + [new_human_message],
            session_id=session_id,
            error=f"{exc}\n{tb}",
        )
        return result

    # Extract the final AI response
    all_messages: list[BaseMessage] = final_state.get("messages", [])
    final_response = ""
    for msg in reversed(all_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            final_response = str(msg.content)
            break

    if not final_response:
        final_response = "I've processed your request. Is there anything else I can help you with?"

    routed_agent = final_state.get("routed_agent")
    tool_trace = final_state.get("tool_trace", [])

    # Async audit log (best-effort)
    try:
        _log_agent_actions(
            session_id=session_id,
            user_id=user_id,
            user_message=message,
            tool_trace=tool_trace,
            final_response=final_response,
        )
    except Exception:
        pass

    return AetherAgentResult(
        response=final_response,
        routed_agent=routed_agent,
        tool_trace=tool_trace,
        all_messages=all_messages,
        session_id=session_id,
        error=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 11.  CLI test harness (python agent.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Force UTF-8 on Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    print("\n=== AETHER INDIA — Multi-Agent CLI Test ===")
    print("Type 'exit' to quit | 'new' to reset session\n")

    history: list[BaseMessage] = []
    sid = str(uuid.uuid4())

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        if user_input.lower() == "new":
            history = []
            sid = str(uuid.uuid4())
            print("[Session reset]\n")
            continue

        result = run_agent(
            message=user_input,
            user_id=1,  # demo customer: Aarav Sharma
            session_id=sid,
            conversation_history=history,
        )

        print(f"\nAgent: {result.response}")
        print(f"\n[Trace] {result.to_dict()['trace_badge']}")
        if result.tool_trace:
            for entry in result.tool_trace:
                tool = entry.get('tool', '-')
                inp = entry.get('input_summary', '')
                out = entry.get('output_summary', '')
                print(f"  Tool: {tool}")
                print(f"    In : {inp}")
                print(f"    Out: {out}")
        if result.error:
            print(f"\n[ERROR] {result.error[:200]}")
        print()

        history = result.all_messages
