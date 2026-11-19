"""
seed.py — Populates the SQLite database with demo data for AETHER INDIA.

Run from the backend/ directory:
    python seed.py

What this script creates:
    • 2 Users       — 1 customer (Aarav Sharma) + 1 admin
    • 8 Products    — luxury streetwear catalog with INR pricing & per-size stock
    • 4 Orders      — pre-built to exercise all 4 agents out of the box
    • 6 OrderItems  — line items across the 4 orders
    • 2 Notifications — welcome + order dispatched
    • 1 ApprovalRequest — pre-seeded HITL ticket for the Gore-Tex jacket refund

All demo passwords are:  Demo@1234
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Resolve imports when running directly from backend/ ──────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Force UTF-8 output on Windows so emoji / special chars don't crash
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from db.database import SessionLocal, engine, init_db
from db.models import (
    AgentActionLog,
    ApprovalRequest,
    Notification,
    Order,
    OrderItem,
    Product,
    User,
)

# ── Password hashing ──────────────────────────────────────────────────────────
# Use a simple but safe SHA-256 + salt scheme that works on all Python versions
# without passlib/bcrypt compatibility issues. FastAPI auth (Phase 3) will use
# the same helper so login works identically.

def _hash(password: str) -> str:
    """Deterministic SHA-256 hash for demo seeds. FastAPI will use the same."""
    salt = "AETHER_DEMO_SALT_2024"
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


# ─────────────────────────────────────────────────────────────────────────────
# SEED FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────


def seed_users(db: Session) -> dict[str, User]:
    """Create 1 customer + 1 admin. Returns mapping of role -> User object."""
    existing_emails = {u.email for u in db.query(User).all()}

    users: dict[str, User] = {}

    # ── Customer ──────────────────────────────────────────────────────────────
    if "aarav@customer.com" not in existing_emails:
        customer = User(
            name="Aarav Sharma",
            email="aarav@customer.com",
            password_hash=_hash("Demo@1234"),
            role="customer",
            default_address=(
                "Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010"
            ),
            is_active=True,
        )
        db.add(customer)
        db.flush()
        users["customer"] = customer
        print(f"  [+] User created: {customer.email}")
    else:
        users["customer"] = db.query(User).filter_by(email="aarav@customer.com").first()
        print(f"  [=] User already exists: aarav@customer.com")

    # ── Admin ─────────────────────────────────────────────────────────────────
    if "admin@aether.in" not in existing_emails:
        admin = User(
            name="Priya Menon",
            email="admin@aether.in",
            password_hash=_hash("Demo@1234"),
            role="admin",
            default_address="AETHER INDIA Pvt. Ltd., 14B Koregaon Park, Pune, MH - 411001",
            is_active=True,
        )
        db.add(admin)
        db.flush()
        users["admin"] = admin
        print(f"  [+] Admin created: {admin.email}")
    else:
        users["admin"] = db.query(User).filter_by(email="admin@aether.in").first()
        print(f"  [=] Admin already exists: admin@aether.in")

    return users


def seed_products(db: Session) -> dict[str, Product]:
    """
    Create 8 streetwear products with ₹ pricing and per-size stock.
    Returns mapping of SKU -> Product object.
    """
    catalog = [
        {
            "sku": "AETH-HD-480-BLK",
            "name": "AETHER 480GSM Heavyweight Boxy Hoodie",
            "category": "Hoodies",
            "price_inr": 3499.0,
            "sizes_json": json.dumps({"S": 8, "M": 14, "L": 10, "XL": 6}),
            "fit_type": "Boxy",
            "fabric_gsm": 480,
            "style_tags": "heavyweight,boxy,acid-wash,oversized,premium-cotton",
            "image_url": "/images/products/hoodie-480gsm-black.jpg",
            "description": (
                "Our flagship piece. 100% ring-spun combed cotton, 480GSM fleece-back "
                "construction with a structured boxy silhouette. Features a double-layered "
                "kangaroo pocket, flat-lock seams, and a garment-washed finish for an "
                "authentic worn-in feel. Drop shoulder with extended hem — built to be a "
                "statement, not an afterthought."
            ),
        },
        {
            "sku": "AETH-CRG-RPSTOP-OLV",
            "name": "Tactical Ripstop Parachute Cargo Pants",
            "category": "Bottoms",
            "price_inr": 2999.0,
            "sizes_json": json.dumps({"S": 6, "M": 10, "L": 8, "XL": 4}),
            "fit_type": "Relaxed",
            "fabric_gsm": 220,
            "style_tags": "cargo,ripstop,tactical,utility,olive,techwear",
            "image_url": "/images/products/cargo-ripstop-olive.jpg",
            "description": (
                "Engineered for urban mobility. 220GSM ripstop nylon-cotton blend "
                "with DWR (Durable Water Repellency) finish. Features 8 functional pockets "
                "(including 2 hidden zip pockets), adjustable ankle tabs, articulated "
                "knee panels, and MOLLE-compatible D-rings. Relaxed fit with a tapered "
                "ankle — the definitive techwear cargo."
            ),
        },
        {
            "sku": "AETH-TEE-ACIDWSH-WHT",
            "name": "Vintage Acid-Wash Oversized Graphic Tee",
            "category": "Tees",
            "price_inr": 1699.0,
            "sizes_json": json.dumps({"S": 20, "M": 25, "L": 18, "XL": 12}),
            "fit_type": "Oversized",
            "fabric_gsm": 240,
            "style_tags": "acid-wash,graphic,oversized,vintage,streetwear,unisex",
            "image_url": "/images/products/tee-acidwash-white.jpg",
            "description": (
                "240GSM 100% combed cotton with an individual acid-wash process — "
                "every piece is unique. Features a large hand-screen printed graphic "
                "on the chest and a smaller back print. Oversized drop-shoulder cut "
                "with a curved hem. The workhorse of the AETHER wardrobe."
            ),
        },
        {
            "sku": "AETH-JKT-GORETEX-BLK",
            "name": "Apex 3-Layer Gore-Tex Technical Shell Jacket",
            "category": "Outerwear",
            "price_inr": 7999.0,
            "sizes_json": json.dumps({"S": 4, "M": 6, "L": 5, "XL": 3}),
            "fit_type": "Relaxed",
            "fabric_gsm": 180,
            "style_tags": "gore-tex,technical,shell,waterproof,outerwear,premium",
            "image_url": "/images/products/jacket-goretex-black.jpg",
            "description": (
                "GORE-TEX® certified 3-layer construction. 100% waterproof, windproof, "
                "and breathable. Features a helmet-compatible hood with single-hand "
                "adjustment, underarm venting zips, 5 exterior pockets, 2 interior "
                "mesh pockets, and a packable design (folds into the chest pocket). "
                "Seam-taped throughout. Built for the city and the mountain."
            ),
        },
        {
            "sku": "AETH-DNM-CRPNTR-IND",
            "name": "Distressed Denim Carpenter Jeans",
            "category": "Bottoms",
            "price_inr": 3299.0,
            "sizes_json": json.dumps({"S": 7, "M": 12, "L": 9, "XL": 5}),
            "fit_type": "Relaxed",
            "fabric_gsm": 380,
            "style_tags": "denim,carpenter,distressed,relaxed,workwear,indigo",
            "image_url": "/images/products/jeans-carpenter-indigo.jpg",
            "description": (
                "380GSM 12oz selvedge-inspired denim with authentic hand-distressing. "
                "Carpenter loop on the left thigh, dual hammer loops, dual coin pockets, "
                "and an extra deep back patch pocket. Relaxed fit through the thigh with "
                "a straight leg and raw-cut hem. The intersection of workwear and streetwear."
            ),
        },
        {
            "sku": "AETH-PLO-STRUCT-NVY",
            "name": "AETHER Structured Boxy Polo",
            "category": "Tees",
            "price_inr": 2199.0,
            "sizes_json": json.dumps({"S": 12, "M": 18, "L": 15, "XL": 8}),
            "fit_type": "Boxy",
            "fabric_gsm": 260,
            "style_tags": "polo,structured,boxy,navy,premium,luxury-casual",
            "image_url": "/images/products/polo-structured-navy.jpg",
            "description": (
                "260GSM pique cotton polo with a boxy structured silhouette. "
                "Ribbed collar and cuffs, 3-button placket with tonal buttons, "
                "chest tonal embroidered AETHER logotype, and a split hem. "
                "The refined core of a streetwear wardrobe."
            ),
        },
        {
            "sku": "AETH-SWT-CREW-CHR",
            "name": "AETHER Pigment-Dyed Crew Neck Sweatshirt",
            "category": "Hoodies",
            "price_inr": 2699.0,
            "sizes_json": json.dumps({"S": 10, "M": 16, "L": 12, "XL": 7}),
            "fit_type": "Oversized",
            "fabric_gsm": 380,
            "style_tags": "crewneck,sweatshirt,pigment-dyed,charcoal,heavyweight,essentials",
            "image_url": "/images/products/crewneck-pigment-charcoal.jpg",
            "description": (
                "380GSM French terry fleece with an individual pigment-dye process for "
                "a unique tonal variation on every piece. Features a reinforced crew neck "
                "with 2x2 ribbing, set-in sleeves, and a curved hem. "
                "Oversized fit, slightly dropped shoulder. The essential layering piece."
            ),
        },
        {
            "sku": "AETH-ACC-BCLAVA-BLK",
            "name": "AETHER Tactical Balaclava Ski Mask",
            "category": "Accessories",
            "price_inr": 999.0,
            "sizes_json": json.dumps({"S": 30, "M": 40, "L": 35, "XL": 25}),
            "fit_type": "Fitted",
            "fabric_gsm": 320,
            "style_tags": "balaclava,ski-mask,accessories,tactical,winter,unisex",
            "image_url": "/images/products/balaclava-black.jpg",
            "description": (
                "320GSM double-layer thermal knit balaclava. Full-face coverage with "
                "a structured eye cutout and adjustable nose/mouth opening. "
                "Moisture-wicking interior lining. One-size construction with internal "
                "elastic band — fits adult S through XL heads. The finishing touch for "
                "any AETHER winter look."
            ),
        },
    ]

    existing_skus = {p.sku for p in db.query(Product).all()}
    products: dict[str, Product] = {}

    for item in catalog:
        if item["sku"] not in existing_skus:
            product = Product(**item)
            db.add(product)
            db.flush()
            products[item["sku"]] = product
            print(f"  [+] Product: {item['name']} (₹{item['price_inr']})")
        else:
            p = db.query(Product).filter_by(sku=item["sku"]).first()
            products[item["sku"]] = p
            print(f"  [=] Product already exists: {item['sku']}")

    return products


def seed_orders(
    db: Session, customer: User, products: dict[str, Product]
) -> list[Order]:
    """
    Create 4 pre-built orders for testing all 4 agents.

    AETH-1001 → Processing, UPI Paid    — Agent 2: instant cancel / address edit
    AETH-1002 → Delivered 3 days ago    — Agent 3+4: auto-refund (≤ ₹5,000)
    AETH-1003 → Delivered 4 days ago    — Agent 3+4 HITL: refund > ₹5,000 escalation
    AETH-1004 → In Transit, BlueDart    — Agent 2: track + block cancellation
    """
    existing_numbers = {o.order_number for o in db.query(Order).all()}

    created_orders: list[Order] = []

    # ─────────────────────────────────────────────────────────────────────────
    # ORDER 1: AETH-1001 — Processing, UPI Paid
    # ─────────────────────────────────────────────────────────────────────────
    if "AETH-1001" not in existing_numbers:
        order1 = Order(
            order_number="AETH-1001",
            user_id=customer.id,
            status="Processing",
            total_amount_inr=1699.0,
            payment_method="UPI",
            payment_status="Paid",
            transaction_id="UPI-TXN-PH2024-88431",
            shipping_address=(
                "Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010"
            ),
            tracking_number=None,
            carrier=None,
            created_at=_days_ago(1),
            delivered_at=None,
        )
        db.add(order1)
        db.flush()

        item1 = OrderItem(
            order_id=order1.id,
            product_id=products["AETH-TEE-ACIDWSH-WHT"].id,
            product_name="Vintage Acid-Wash Oversized Graphic Tee",
            sku="AETH-TEE-ACIDWSH-WHT",
            size="M",
            quantity=1,
            unit_price_inr=1699.0,
        )
        db.add(item1)
        created_orders.append(order1)
        print(f"  [+] Order AETH-1001 (Processing, ₹1,699)")
    else:
        print(f"  [=] Order AETH-1001 already exists")

    # ─────────────────────────────────────────────────────────────────────────
    # ORDER 2: AETH-1002 — Delivered 3 days ago, UPI Paid (auto-refund eligible)
    # ─────────────────────────────────────────────────────────────────────────
    if "AETH-1002" not in existing_numbers:
        delivered2 = _days_ago(3)
        order2 = Order(
            order_number="AETH-1002",
            user_id=customer.id,
            status="Delivered",
            total_amount_inr=3499.0,
            payment_method="UPI",
            payment_status="Paid",
            transaction_id="UPI-TXN-GP2024-54921",
            shipping_address=(
                "Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010"
            ),
            tracking_number="BD10247893421",
            carrier="BlueDart",
            created_at=_days_ago(7),
            delivered_at=delivered2,
        )
        db.add(order2)
        db.flush()

        item2 = OrderItem(
            order_id=order2.id,
            product_id=products["AETH-HD-480-BLK"].id,
            product_name="AETHER 480GSM Heavyweight Boxy Hoodie",
            sku="AETH-HD-480-BLK",
            size="L",
            quantity=1,
            unit_price_inr=3499.0,
        )
        db.add(item2)
        created_orders.append(order2)
        print(f"  [+] Order AETH-1002 (Delivered 3d ago, ₹3,499 — auto-refund eligible)")
    else:
        print(f"  [=] Order AETH-1002 already exists")

    # ─────────────────────────────────────────────────────────────────────────
    # ORDER 3: AETH-1003 — Delivered 4 days ago, Card Paid (HITL escalation)
    # ─────────────────────────────────────────────────────────────────────────
    if "AETH-1003" not in existing_numbers:
        delivered3 = _days_ago(4)
        order3 = Order(
            order_number="AETH-1003",
            user_id=customer.id,
            status="Delivered",
            total_amount_inr=7999.0,
            payment_method="Card",
            payment_status="Paid",
            transaction_id="RZPY-PAY-MxfJK2024-9981",
            shipping_address=(
                "Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010"
            ),
            tracking_number="DLV98342871A",
            carrier="Delhivery",
            created_at=_days_ago(9),
            delivered_at=delivered3,
        )
        db.add(order3)
        db.flush()

        item3 = OrderItem(
            order_id=order3.id,
            product_id=products["AETH-JKT-GORETEX-BLK"].id,
            product_name="Apex 3-Layer Gore-Tex Technical Shell Jacket",
            sku="AETH-JKT-GORETEX-BLK",
            size="M",
            quantity=1,
            unit_price_inr=7999.0,
        )
        db.add(item3)
        created_orders.append(order3)
        print(f"  [+] Order AETH-1003 (Delivered 4d ago, ₹7,999 — HITL escalation)")
    else:
        print(f"  [=] Order AETH-1003 already exists")

    # ─────────────────────────────────────────────────────────────────────────
    # ORDER 4: AETH-1004 — In Transit via BlueDart
    # ─────────────────────────────────────────────────────────────────────────
    if "AETH-1004" not in existing_numbers:
        order4 = Order(
            order_number="AETH-1004",
            user_id=customer.id,
            status="In Transit",
            total_amount_inr=2999.0,
            payment_method="COD",
            payment_status="Pending",
            transaction_id=None,
            shipping_address=(
                "Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010"
            ),
            tracking_number="BD20458173902",
            carrier="BlueDart",
            created_at=_days_ago(3),
            delivered_at=None,
        )
        db.add(order4)
        db.flush()

        item4 = OrderItem(
            order_id=order4.id,
            product_id=products["AETH-CRG-RPSTOP-OLV"].id,
            product_name="Tactical Ripstop Parachute Cargo Pants",
            sku="AETH-CRG-RPSTOP-OLV",
            size="M",
            quantity=1,
            unit_price_inr=2999.0,
        )
        db.add(item4)
        created_orders.append(order4)
        print(f"  [+] Order AETH-1004 (In Transit via BlueDart, ₹2,999 COD)")
    else:
        print(f"  [=] Order AETH-1004 already exists")

    return created_orders


def seed_notifications(db: Session, customer: User) -> None:
    """Seed 2 welcome / order notifications for the customer."""
    existing_count = (
        db.query(Notification).filter_by(user_id=customer.id).count()
    )
    if existing_count > 0:
        print(f"  [=] Notifications already exist for user {customer.id}")
        return

    notifs = [
        Notification(
            user_id=customer.id,
            title="Welcome to AETHER INDIA! 🖤",
            message=(
                "Your account is active. Explore our latest streetwear drops and "
                "enjoy free shipping on orders above ₹1,999."
            ),
            notification_type="GENERAL",
            is_read=False,
            created_at=_days_ago(10),
        ),
        Notification(
            user_id=customer.id,
            title="Order Shipped — AETH-1004",
            message=(
                "Your Tactical Ripstop Cargo Pants have been dispatched via BlueDart. "
                "Tracking ID: BD20458173902. Estimated delivery: 2–3 business days."
            ),
            notification_type="ORDER_SHIPPED",
            is_read=False,
            created_at=_days_ago(3),
        ),
        Notification(
            user_id=customer.id,
            title="Order Delivered — AETH-1002 ✅",
            message=(
                "Your AETHER 480GSM Heavyweight Boxy Hoodie has been delivered. "
                "We hope you love it! For returns or exchanges, chat with us within 14 days."
            ),
            notification_type="GENERAL",
            is_read=True,
            created_at=_days_ago(3),
        ),
    ]

    for n in notifs:
        db.add(n)

    print(f"  [+] Created {len(notifs)} notifications for {customer.email}")


def seed_hitl_approval(
    db: Session, customer: User, orders: list[Order]
) -> None:
    """
    Seed a pre-existing PENDING_ADMIN ApprovalRequest for AETH-1003
    (₹7,999 Gore-Tex Jacket refund — above the ₹5,000 HITL threshold).
    This makes the Admin Dashboard HITL queue non-empty on first load.
    """
    # Find AETH-1003 order
    order3: Order | None = next(
        (o for o in orders if o.order_number == "AETH-1003"), None
    )
    if order3 is None:
        order3 = db.query(Order).filter_by(order_number="AETH-1003").first()

    if order3 is None:
        print("  [!] AETH-1003 not found; skipping ApprovalRequest seed.")
        return

    existing = (
        db.query(ApprovalRequest)
        .filter_by(order_number="AETH-1003")
        .first()
    )
    if existing:
        print(f"  [=] ApprovalRequest for AETH-1003 already exists")
        return

    approval = ApprovalRequest(
        order_id=order3.id,
        order_number="AETH-1003",
        user_id=customer.id,
        action_type="HIGH_VALUE_REFUND",
        amount_inr=7999.0,
        reason=(
            "Customer reports that the Gore-Tex jacket's DWR coating failed after first use. "
            "Water is no longer beading on the outer shell despite following care instructions."
        ),
        ai_summary=(
            "Customer Aarav Sharma (aarav@customer.com) is requesting a full refund of ₹7,999 "
            "for Order AETH-1003 (Apex 3-Layer Gore-Tex Technical Shell Jacket, Size M). "
            "Reason: DWR coating failure after first use. Order was delivered 4 days ago, "
            "within the 14-day return window. Refund amount exceeds the ₹5,000 auto-approval "
            "threshold. AI verified that the item is eligible based on delivery date and "
            "policy, but escalating to admin for financial authorization. "
            "Payment method: Card (Razorpay TXN: RZPY-PAY-MxfJK2024-9981)."
        ),
        status="PENDING_ADMIN",
        admin_notes=None,
        created_at=_days_ago(0),
    )
    db.add(approval)
    print(f"  [+] ApprovalRequest created for AETH-1003 (₹7,999 — PENDING_ADMIN)")


def seed_agent_log_sample(db: Session, customer: User) -> None:
    """Seed a few sample AgentActionLog entries for the Admin Audit Log page."""
    existing_count = (
        db.query(AgentActionLog).filter_by(user_id=customer.id).count()
    )
    if existing_count > 0:
        print(f"  [=] AgentActionLog entries already exist; skipping.")
        return

    sample_logs = [
        AgentActionLog(
            session_id="demo-session-0001",
            user_id=customer.id,
            user_message="What is your return policy?",
            routed_agent="CustomerSupportAgent",
            tool_called="query_brand_knowledge_rag",
            tool_input=json.dumps({"query": "return policy refund rules"}),
            tool_output=json.dumps({
                "source": "return_policy.md",
                "result": "14-day return window. Auto-refund for amounts ≤ ₹5,000. "
                          "HITL escalation for amounts > ₹5,000.",
            }),
            final_response=(
                "AETHER INDIA offers a 14-day return window from delivery. "
                "Refunds of ₹5,000 or below are automatically processed within "
                "3–5 business days. Amounts above ₹5,000 require admin approval "
                "within 48 hours."
            ),
            created_at=_days_ago(2),
        ),
        AgentActionLog(
            session_id="demo-session-0002",
            user_id=customer.id,
            user_message="Track my order AETH-1004",
            routed_agent="OrderAndInventoryAgent",
            tool_called="check_order_status",
            tool_input=json.dumps({"order_number": "AETH-1004", "user_id": customer.id}),
            tool_output=json.dumps({
                "order_number": "AETH-1004",
                "status": "In Transit",
                "carrier": "BlueDart",
                "tracking_number": "BD20458173902",
                "eta": "2–3 business days",
            }),
            final_response=(
                "Your Cargo Pants (AETH-1004) are currently In Transit via BlueDart. "
                "Tracking ID: BD20458173902. Estimated delivery in 2–3 business days "
                "to your Indore address."
            ),
            created_at=_days_ago(1),
        ),
        AgentActionLog(
            session_id="demo-session-0003",
            user_id=customer.id,
            user_message="I want a refund for my Gore-Tex jacket order AETH-1003",
            routed_agent="RefundAndPaymentAgent",
            tool_called="process_refund_or_exchange",
            tool_input=json.dumps({
                "order_number": "AETH-1003",
                "item_sku": "AETH-JKT-GORETEX-BLK",
                "action_type": "REFUND",
                "reason": "DWR coating failure after first use",
            }),
            tool_output=json.dumps({
                "result": "ESCALATED",
                "reason": "Refund amount ₹7,999 exceeds auto-approval threshold of ₹5,000.",
                "approval_request_id": 1,
            }),
            final_response=(
                "Your refund request of ₹7,999 for the Gore-Tex Jacket (AETH-1003) "
                "has been escalated to our operations team for approval. You will receive "
                "a decision within 24–48 hours. An in-app notification has been sent."
            ),
            created_at=_days_ago(0),
        ),
    ]

    for log in sample_logs:
        db.add(log)

    print(f"  [+] Created {len(sample_logs)} sample AgentActionLog entries")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 60)
    print("  AETHER INDIA — Database Seed Script")
    print("=" * 60)

    # Ensure all tables exist
    print("\n[1/7] Initialising database tables...")
    init_db()
    print("  Tables created / verified.")

    db: Session = SessionLocal()
    try:
        # ── Users ─────────────────────────────────────────────────────────────
        print("\n[2/7] Seeding users...")
        users = seed_users(db)
        customer: User = users["customer"]

        # ── Products ──────────────────────────────────────────────────────────
        print("\n[3/7] Seeding products (8 items)...")
        products = seed_products(db)

        # ── Orders ────────────────────────────────────────────────────────────
        print("\n[4/7] Seeding 4 demo orders...")
        orders = seed_orders(db, customer, products)

        # ── Notifications ────────────────────────────────────────────────────
        print("\n[5/7] Seeding notifications...")
        seed_notifications(db, customer)

        # ── HITL ApprovalRequest ─────────────────────────────────────────────
        print("\n[6/7] Seeding HITL approval request...")
        seed_hitl_approval(db, customer, orders)

        # ── Agent Audit Logs ─────────────────────────────────────────────────
        print("\n[7/7] Seeding sample agent audit logs...")
        seed_agent_log_sample(db, customer)

        # ── Commit ────────────────────────────────────────────────────────────
        db.commit()
        print("\n" + "=" * 60)
        print("  ✅  Seed complete! Database is ready for demonstration.")
        print("=" * 60)
        print("\nDemo Credentials:")
        print("  Customer  →  aarav@customer.com   /  Demo@1234")
        print("  Admin     →  admin@aether.in      /  Demo@1234")
        print("\nSQLite file: aether_store.db")
        print("=" * 60 + "\n")

    except Exception as exc:
        db.rollback()
        print(f"\n  [FAILED] Seed failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
