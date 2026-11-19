# AETHER INDIA — Autonomous AI Business Operations Agent
**Implementation Domain:** Luxury Streetwear & Apparel E-Commerce Platform  
**Architecture:** 4-Agent LangGraph Multi-Agent System with Local SQLite & ChromaDB RAG  

---

## 1. System Overview

AETHER INDIA is an autonomous business operations platform designed for final-year engineering project demonstration. It combines a high-contrast luxury streetwear storefront with a **4-Agent LangGraph Supervisor multi-agent architecture** that autonomously handles:
- **Product Styling & Brand Knowledge RAG** (Free local embeddings over policy & sizing manuals)
- **Live Order Creation, Stock Control & Real-time Cancellation** (BlueDart & Delhivery dispatch)
- **Automated ₹ Refunds vs. Human-in-the-Loop Escalation** (Strict ₹5,000 threshold enforcement)
- **Operations Head Dashboard** (HITL authorization queue, real-time KPI aggregates, stock matrix)

---

## 2. The 4-Agent LangGraph Architecture

```mermaid
flowchart TD
    User([Customer / Operations User]) --> Sup[Supervisor Router Node]

    subgraph MultiAgentSystem [4-Agent LangGraph System]
        Sup -->|Routing| Agent1[Agent 1: CustomerSupportAgent]
        Sup -->|Routing| Agent2[Agent 2: OrderAndInventoryAgent]
        Sup -->|Routing| Agent3[Agent 3: RefundAndPaymentAgent]
        Sup -->|Routing / Handoff| Agent4[Agent 4: NotificationAndEscalationAgent]

        Agent1 -->|ReAct Loop Done| Sup
        Agent2 -->|requires_notification: true| Sup
        Agent3 -->|handoff_to_agent4: true| Sup
        Agent4 -->|Alert / Escalation Ticket Done| Sup
    end

    Sup -->|next_agent = FINISH| Result([Final Chat Response & Audit Log])
```

### Agent Roles & Tool Roster

1. **AGENT 1: `CustomerSupportAgent`**
   - **Role:** Policy Q&A, fit guidance, washing care, and streetwear catalog recommendations.
   - **Tools:** `query_brand_knowledge_rag` (ChromaDB vector store), `search_and_style_products` (catalog query with ₹ price, fit, and size filters).

2. **AGENT 2: `OrderAndInventoryAgent`**
   - **Role:** Direct order placement from chat, live parcel tracking, stock validation, and cancellation rules.
   - **Tools:** `create_new_order` (atomically decrements stock and creates `AETH-XXXX`), `check_inventory_and_add_to_cart`, `check_order_status`, `cancel_or_modify_order` (permits cancellation only for `Processing`/`Packed`; restores stock).

3. **AGENT 3: `RefundAndPaymentAgent`**
   - **Role:** Payment verification (UPI/Card TXNs), size exchanges with RMA generation, and automated refund tier enforcement.
   - **Tools:** `check_payment_and_refund_status`, `process_refund_or_exchange` (**₹5,000 Threshold:** ≤ ₹5k auto-approved; > ₹5k flagged for HITL admin review).

4. **AGENT 4: `NotificationAndEscalationAgent`**
   - **Role:** Real-time customer alerts and Human-in-the-Loop ticket generation.
   - **Tools:** `send_customer_notification` (writes to `Notification` table for the customer bell drawer), `escalate_to_human_admin` (creates `PENDING_ADMIN` ticket in `ApprovalRequest`).

---

## 3. Tech Stack & Zero-Cost Local Design

| Layer | Technology | Cost / Offline Guarantee |
|---|---|---|
| **Frontend** | Next.js 14+ (App Router, TypeScript), Tailwind CSS, Lucide React, Zustand | 100% Local (`http://localhost:3000`) |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy (SQLite), Pydantic v2 | 100% Local (`http://localhost:8000`) |
| **Multi-Agent Core** | LangGraph (`StateGraph`), LangChain | Configurable for Google Gemini (`gemini-2.5-flash`) or Groq (`llama-3.3-70b-versatile`) |
| **RAG Vector Store** | ChromaDB (`./chroma_db`) + `sentence-transformers/all-MiniLM-L6-v2` | 100% Free / Local CPU inference (0 API quota used) |
| **Relational Database** | SQLite (`aether_store.db`) with WAL mode & Foreign Keys enabled | 100% Local |

---

## 4. Demo Portals & Seeded Credentials

### 🛍️ Customer Portal (`http://localhost:3000`)
- **Credentials:** `aarav@customer.com` / `Demo@1234` (Available via 1-Click login button at `/login`)
- **Default Address:** `Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010`
- **Pre-Seeded Orders to Test Every Agent:**
  1. `AETH-1001` (₹1,699, `Processing`, UPI Paid) ➔ Tests **Agent 2** (instant cancel or address change).
  2. `AETH-1002` (₹3,499, `Delivered`, UPI Paid) ➔ Tests **Agent 3 + 4** (auto-refund because ₹3,499 ≤ ₹5,000, or size exchange).
  3. `AETH-1003` (₹7,999 Gore-Tex Jacket, `Delivered`, Card Paid) ➔ Tests **Agent 3 + 4 HITL Escalation** (refund > ₹5,000 creates Admin ticket).
  4. `AETH-1004` (₹2,999 Cargo Pants, `In Transit` via BlueDart) ➔ Tests **Agent 2** (live tracking + blocks cancellation).

### 🛡️ Admin Operations Dashboard (`http://localhost:3000/admin`)
- **Credentials:** `admin@aether.in` / `Demo@1234` (Available via 1-Click login button at `/login`)
- **Sub-Modules:**
  - `/admin`: Revenue in ₹, Total Orders, AI Resolved vs Escalated ratio, and Pending review alerts.
  - `/admin/approvals`: **HITL Approval Queue** to approve or reject > ₹5,000 refunds (e.g. AETH-1003).
  - `/admin/orders`: Order & Carrier tracking management (`Processing` ➔ `In Transit` ➔ `Delivered`).
  - `/admin/inventory`: Live size stock matrix (`S, M, L, XL`) with direct restock controls.
  - `/admin/agent-logs`: Full multi-agent audit trail with expandable tool inputs and RAG outputs.

---

## 5. Quick Start Instructions

### ⚡ 1-Click Launch (Windows — Recommended)
Simply double-click the batch files in the project folder:
- **`START.bat`**: Double-click to run! (Automatically checks dependencies, starts both backend and frontend, and automatically opens `http://localhost:3000` in your browser).
- **`STOP.bat`**: Double-click to cleanly terminate all running servers.
- **`SETUP.bat`**: Double-click to run one-time installation on a fresh laptop.

---

### Manual Setup & Run (Command Line)

#### A. Fresh Setup (First Time After Cloning)

```powershell
# 1. Backend Setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure your API keys (copy example and edit)
Copy-Item .env.example .env
# Edit .env and paste your GOOGLE_API_KEY and/or GROQ_API_KEY

# Seed the database and build local ChromaDB embeddings
python seed.py

# 2. Frontend Setup
cd ..\frontend
npm install
```

#### B. Everyday Run (Command Line)

From the project root:
```powershell
.\run_project.ps1
```

Or start both services individually in two terminals:

```powershell
# Terminal 1 — Backend:
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Frontend:
cd frontend
cmd /c npm run dev
```

---

## 6. Project Demonstration Walkthrough (For Evaluators)

1. **Storefront & UI Order Checkout:**
   - Go to `http://localhost:3000`, select size `L` on the *AETHER 480GSM Boxy Hoodie*, click **Add to Cart**.
   - Navigate to `/cart`, choose UPI, and click **Place Order**.
   - Show that the order is immediately created in SQLite and visible on `/orders`.

2. **Order Placement via Autonomous AI Chat:**
   - Click the **AI Concierge** button on the bottom right.
   - Type: *"Buy the Vintage Acid-Wash Oversized Graphic Tee in size M using UPI"*.
   - Watch the **Execution Trace Badge** display: `Supervisor → OrderAndInventoryAgent → create_new_order`.
   - The AI confirms order creation with an interactive Order Card.

3. **Autonomous Refund (≤ ₹5,000):**
   - In chat, type: *"I want to return order AETH-1002"*.
   - Watch the AI auto-approve the refund of ₹3,499 and hand off to Agent 4 to emit a notification in the customer bell drawer.

4. **Human-in-the-Loop (HITL) Escalation (> ₹5,000):**
   - In chat, type: *"I want a refund for my Gore-Tex jacket order AETH-1003"*.
   - Because the jacket is ₹7,999 (> ₹5,000 threshold), the AI informs the customer that the case is escalated for Operations Head approval.
   - Switch to the Admin Dashboard (`http://localhost:3000/admin/approvals`).
   - Show Ticket #1 for AETH-1003 with the AI synthesized case summary.
   - Click **"Approve & Issue ₹7,999 Refund"**. The status changes to `Refunded` and a notification is dispatched to Aarav Sharma.
