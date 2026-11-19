"""
tools.py — All LangChain tools for the AETHER INDIA 4-Agent System.

Tool roster
-----------
Agent 1 — CustomerSupportAgent
    • query_brand_knowledge_rag        (RAG search over 4 policy docs)
    • search_and_style_products        (catalog search with filters)

Agent 2 — OrderAndInventoryAgent
    • create_new_order                 (full order creation in SQLite)
    • check_inventory_and_add_to_cart  (stock validation + cart payload)
    • check_order_status               (live tracking & ETA)
    • cancel_or_modify_order           (cancel / address-edit with rules)

Agent 3 — RefundAndPaymentAgent
    • check_payment_and_refund_status  (payment & refund state)
    • process_refund_or_exchange       (₹5,000 threshold logic + HITL)

Agent 4 — NotificationAndEscalationAgent
    • send_customer_notification       (writes Notification record)
    • escalate_to_human_admin          (creates ApprovalRequest + notifies)

All tools return plain strings — either JSON-encoded structured data or
human-readable messages — so the agent LLM can process them reliably.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from langchain_core.tools import tool
from sqlalchemy.orm import Session

load_dotenv()

# ── Bootstrap sys.path so tools.py works from any working directory ──────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from db.database import SessionLocal
from db.models import (
    AgentActionLog,
    ApprovalRequest,
    Notification,
    Order,
    OrderItem,
    Product,
    User,
)

# Import the RAG query function (lazy so ChromaDB doesn't initialise at import)
from rag_engine import query_brand_knowledge_rag as _rag_query

AUTO_REFUND_THRESHOLD_INR: float = float(
    __import__("os").getenv("AUTO_REFUND_THRESHOLD_INR", "5000")
)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def _db():
    """Yield a SQLAlchemy session and ensure it is closed afterwards."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


def _make_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is UTC-aware. SQLite returns naive datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _generate_order_number(session: Session) -> str:
    """Find the current max AETH-XXXX number and return the next one."""
    orders = session.query(Order.order_number).all()
    max_num = 1000
    for (num_str,) in orders:
        if isinstance(num_str, str) and num_str.startswith("AETH-"):
            try:
                max_num = max(max_num, int(num_str.split("-")[1]))
            except (ValueError, IndexError):
                pass
    return f"AETH-{max_num + 1:04d}"


def _generate_rma_number(session: Session) -> str:
    """Generate a unique RMA label number."""
    count = session.query(ApprovalRequest).count()
    return f"RMA-{count + 1001:04d}"


def _generate_tracking_number(carrier: str) -> str:
    """Simulate a carrier tracking number."""
    prefix = "BD" if carrier == "BlueDart" else "DLV"
    return f"{prefix}{random.randint(10000000000, 99999999999)}"


def _carrier_for_address(address: str) -> str:
    """Assign carrier based on city keyword in address."""
    metro_keywords = [
        "mumbai", "delhi", "bengaluru", "bangalore", "chennai",
        "hyderabad", "kolkata", "pune", "ahmedabad",
    ]
    addr_lower = address.lower()
    if any(city in addr_lower for city in metro_keywords):
        return "BlueDart"
    return "Delhivery"


def _eta_days_for_carrier(carrier: str, address: str) -> str:
    """Return human-readable ETA string."""
    addr_lower = address.lower()
    metro_keywords = [
        "mumbai", "delhi", "bengaluru", "bangalore", "chennai",
        "hyderabad", "kolkata", "pune", "ahmedabad",
    ]
    if any(city in addr_lower for city in metro_keywords):
        return "2–3 business days" if carrier == "BlueDart" else "3–4 business days"
    return "4–6 business days"


def _generate_transaction_id(method: str) -> str:
    """Simulate a payment transaction ID."""
    if method.upper() == "UPI":
        return f"UPI-TXN-{random.randint(10000000, 99999999)}"
    elif method.upper() in ("CARD", "CREDIT/DEBIT CARD"):
        return f"RZPY-PAY-{hashlib.md5(str(random.random()).encode()).hexdigest()[:12].upper()}"
    return ""  # COD has no upfront transaction ID


def _order_to_dict(order: Order) -> dict:
    """Serialise an Order + its items to a plain dict for tool return."""
    items = [
        {
            "product_name": it.product_name,
            "sku": it.sku,
            "size": it.size,
            "quantity": it.quantity,
            "unit_price_inr": it.unit_price_inr,
            "subtotal_inr": it.subtotal_inr,
        }
        for it in order.items
    ]
    return {
        "order_number": order.order_number,
        "status": order.status,
        "total_amount_inr": order.total_amount_inr,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "transaction_id": order.transaction_id,
        "shipping_address": order.shipping_address,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "items": items,
    }


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 1 TOOLS — CustomerSupportAgent
# ─────────────────────────────────────────────────────────────────────────────

@tool
def query_brand_knowledge_rag(query: str) -> str:
    """
    Search the AETHER INDIA brand knowledge base using semantic RAG retrieval.

    Use this tool to answer questions about:
    - Return and refund policies (including the ₹5,000 auto-refund threshold)
    - Size and fit guides (Boxy vs Oversized, measurements in cm and inches)
    - Fabric care instructions (GSM-based washing, drying, ironing)
    - Shipping SLAs (BlueDart / Delhivery ETAs by city, cancellation rules)

    Args:
        query: The customer's question in natural language.

    Returns:
        Relevant policy excerpts from the knowledge base with source attribution.
    """
    try:
        return _rag_query(query, n_results=4)
    except Exception as exc:
        return f"RAG query failed: {exc}. Please answer from general brand knowledge."


@tool
def search_and_style_products(
    query: str,
    category: Optional[str] = None,
    max_price_inr: Optional[float] = None,
    size: Optional[str] = None,
) -> str:
    """
    Search the AETHER INDIA product catalog and return styled product cards.

    Use this tool to recommend products, check what's available, or help a
    customer find items that match their style preferences or budget.

    Args:
        query:         Free-text search query (product name, style tags, fabric).
        category:      Optional filter — one of: Hoodies, Tees, Bottoms, Outerwear, Accessories
        max_price_inr: Optional maximum price in Indian Rupees.
        size:          Optional size filter — one of: S, M, L, XL

    Returns:
        JSON array of matching product cards with price (₹), stock info, and
        style details, or a message if no products match.
    """
    with _db() as db:
        q = db.query(Product).filter(Product.is_active == True)

        if category:
            q = q.filter(Product.category.ilike(f"%{category}%"))
        if max_price_inr is not None:
            q = q.filter(Product.price_inr <= max_price_inr)

        products = q.all()

        # Apply text search across name, description, and style_tags
        query_lower = query.lower()
        keywords = [kw.strip() for kw in query_lower.split() if len(kw.strip()) > 2]

        if keywords:
            matched = []
            for p in products:
                searchable = " ".join([
                    p.name or "",
                    p.description or "",
                    p.style_tags or "",
                    p.category or "",
                    p.fit_type or "",
                ]).lower()
                if any(kw in searchable for kw in keywords):
                    matched.append(p)
            products = matched if matched else products  # fallback to unfiltered if no match

        # Apply size filter
        if size:
            size_upper = size.upper()
            products = [p for p in products if p.get_stock_for_size(size_upper) > 0]

        if not products:
            return (
                f"No products found matching your criteria. "
                f"Try browsing our full catalog at /shop or ask me to suggest "
                f"something specific."
            )

        cards = []
        for p in products[:6]:  # Cap at 6 results to stay within context limits
            sizes_info = p.sizes
            in_stock_sizes = [s for s, qty in sizes_info.items() if qty > 0]
            cards.append({
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "price_inr": p.price_inr,
                "price_formatted": f"₹{p.price_inr:,.0f}",
                "fit_type": p.fit_type,
                "fabric_gsm": p.fabric_gsm,
                "style_tags": p.style_tags,
                "description": (p.description or "")[:220] + "…"
                if p.description and len(p.description) > 220
                else p.description,
                "image_url": p.image_url,
                "in_stock_sizes": in_stock_sizes,
                "stock_by_size": sizes_info,
                "total_stock": p.total_stock,
            })

        return json.dumps({"products": cards, "total_found": len(cards)}, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 2 TOOLS — OrderAndInventoryAgent
# ─────────────────────────────────────────────────────────────────────────────

@tool
def create_new_order(
    user_id: int,
    product_sku: str,
    size: str,
    quantity: int,
    shipping_address: str,
    payment_method: str,
) -> str:
    """
    Place a new order directly from the AI chat on behalf of the customer.

    Validates live stock, decrements inventory, creates Order + OrderItem records
    in SQLite with a unique AETH-XXXX order number, assigns a carrier, and
    returns a full Order Confirmation Card for display in the chat.

    Args:
        user_id:          The authenticated customer's user ID.
        product_sku:      Product SKU (e.g. 'AETH-HD-480-BLK').
        size:             Size to order — one of: S, M, L, XL
        quantity:         Number of units (must be >= 1).
        shipping_address: Full delivery address as a string.
        payment_method:   One of: UPI, Card, COD

    Returns:
        JSON with order confirmation details, or an error message if the
        order cannot be placed (out of stock, invalid SKU, etc.).
    """
    size = size.upper().strip()
    payment_method = payment_method.strip()

    # Validate quantity
    if quantity < 1:
        return json.dumps({"error": "Quantity must be at least 1."})

    # Normalise payment method
    pm_map = {
        "UPI": "UPI", "GOOGLEPAY": "UPI", "PHONEPAY": "UPI", "PAYTM": "UPI",
        "CARD": "Card", "CREDIT": "Card", "DEBIT": "Card", "CREDIT/DEBIT": "Card",
        "CREDITCARD": "Card", "DEBITCARD": "Card",
        "COD": "COD", "CASH": "COD", "CASHONDELIVERY": "COD",
    }
    pm_key = payment_method.upper().replace(" ", "").replace("/", "")
    normalised_pm = pm_map.get(pm_key, payment_method)

    with _db() as db:
        # Verify user exists
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return json.dumps({"error": f"User ID {user_id} not found."})

        # Look up product
        product = db.query(Product).filter_by(sku=product_sku, is_active=True).first()
        if not product:
            return json.dumps({
                "error": f"Product SKU '{product_sku}' not found in catalog. "
                         f"Use search_and_style_products to find a valid SKU."
            })

        # Check size validity
        valid_sizes = list(product.sizes.keys())
        if size not in valid_sizes:
            return json.dumps({
                "error": f"Size '{size}' is not valid for this product. "
                         f"Available sizes: {valid_sizes}"
            })

        # Check stock
        available_stock = product.get_stock_for_size(size)
        if available_stock < quantity:
            in_stock = [s for s, q in product.sizes.items() if q > 0]
            return json.dumps({
                "error": (
                    f"Insufficient stock for {product.name} in size {size}. "
                    f"Available: {available_stock} unit(s). "
                    f"In-stock sizes: {in_stock}"
                )
            })

        # Generate order details
        order_number = _generate_order_number(db)
        carrier = _carrier_for_address(shipping_address)
        tracking_number = _generate_tracking_number(carrier)
        total_amount = product.price_inr * quantity

        # Payment state
        txn_id = None
        pay_status = "Pending"
        if normalised_pm in ("UPI", "Card"):
            txn_id = _generate_transaction_id(normalised_pm)
            pay_status = "Paid"

        # Create Order
        order = Order(
            order_number=order_number,
            user_id=user_id,
            status="Processing",
            total_amount_inr=total_amount,
            payment_method=normalised_pm,
            payment_status=pay_status,
            transaction_id=txn_id,
            shipping_address=shipping_address,
            tracking_number=tracking_number,
            carrier=carrier,
            created_at=_now(),
            delivered_at=None,
        )
        db.add(order)
        db.flush()  # get order.id

        # Create OrderItem
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            size=size,
            quantity=quantity,
            unit_price_inr=product.price_inr,
        )
        db.add(item)

        # Decrement stock
        product.decrement_stock(size, quantity)

        eta = _eta_days_for_carrier(carrier, shipping_address)

        result = {
            "success": True,
            "order_number": order_number,
            "order_id": order.id,
            "product_name": product.name,
            "sku": product.sku,
            "size": size,
            "quantity": quantity,
            "unit_price_inr": product.price_inr,
            "total_amount_inr": total_amount,
            "total_formatted": f"₹{total_amount:,.0f}",
            "payment_method": normalised_pm,
            "payment_status": pay_status,
            "transaction_id": txn_id,
            "shipping_address": shipping_address,
            "carrier": carrier,
            "tracking_number": tracking_number,
            "estimated_delivery": eta,
            "status": "Processing",
            "message": (
                f"Order {order_number} placed successfully! "
                f"Your {product.name} (Size {size}) worth ₹{total_amount:,.0f} "
                f"will be delivered in {eta} via {carrier}."
            ),
            "requires_notification": True,
        }

        return json.dumps(result, indent=2)


@tool
def check_inventory_and_add_to_cart(
    user_id: int,
    product_id: int,
    size: str,
    quantity: int,
) -> str:
    """
    Validate stock availability for a product/size and return a cart-add payload
    for the frontend. Does NOT create an order — use create_new_order for that.

    Args:
        user_id:    The authenticated customer's user ID.
        product_id: The numeric product ID from the catalog.
        size:       Size to check — one of: S, M, L, XL
        quantity:   Number of units requested.

    Returns:
        JSON with stock availability and a cart payload, or an error if
        the item is out of stock.
    """
    size = size.upper().strip()

    with _db() as db:
        product = db.query(Product).filter_by(id=product_id, is_active=True).first()
        if not product:
            return json.dumps({"error": f"Product ID {product_id} not found."})

        available = product.get_stock_for_size(size)
        if available == 0:
            alt_sizes = [s for s, q in product.sizes.items() if q > 0]
            return json.dumps({
                "error": (
                    f"{product.name} is out of stock in size {size}. "
                    f"Available sizes: {alt_sizes or 'None — item is sold out'}."
                ),
                "can_add_to_cart": False,
            })

        if available < quantity:
            return json.dumps({
                "error": (
                    f"Only {available} unit(s) of {product.name} (Size {size}) "
                    f"in stock. You requested {quantity}."
                ),
                "can_add_to_cart": False,
                "available_quantity": available,
            })

        return json.dumps({
            "can_add_to_cart": True,
            "cart_payload": {
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "size": size,
                "quantity": quantity,
                "unit_price_inr": product.price_inr,
                "image_url": product.image_url,
            },
            "available_stock": available,
            "message": (
                f"✅ {product.name} in size {size} is available "
                f"({available} in stock). Added to cart!"
            ),
        }, indent=2)


@tool
def check_order_status(order_number: str, user_id: int) -> str:
    """
    Fetch the live delivery status, carrier tracking info, and ETA for an order.

    Args:
        order_number: The AETHER order number, e.g. 'AETH-1004'.
        user_id:      The authenticated customer's user ID (for security check).

    Returns:
        JSON with current order status, carrier, tracking number, and ETA.
        Returns an error if the order is not found or belongs to a different user.
    """
    with _db() as db:
        order = db.query(Order).filter_by(order_number=order_number.upper().strip()).first()

        if not order:
            return json.dumps({
                "error": f"Order '{order_number}' not found. Please check the order number."
            })

        if order.user_id != user_id:
            return json.dumps({
                "error": "This order does not belong to your account. "
                         "Please provide your own order number."
            })

        # Compute ETA based on status and created_at
        now = _now()
        created_aware = _make_aware(order.created_at)
        delivered_aware = _make_aware(order.delivered_at)
        eta_str = "N/A"

        if order.status == "Processing":
            dispatch_date = created_aware + timedelta(days=1)
            eta_str = f"Dispatch expected by {dispatch_date.strftime('%d %b %Y')}. Delivery in 4–6 business days."
        elif order.status == "Packed":
            eta_str = "Awaiting carrier pickup. Delivery in 3–5 business days once shipped."
        elif order.status == "In Transit":
            days_since_dispatch = (now - created_aware).days
            remaining = max(1, 6 - days_since_dispatch)
            eta_str = f"Estimated delivery in {remaining}–{remaining + 1} business days."
        elif order.status == "Delivered":
            eta_str = (
                f"Delivered on {delivered_aware.strftime('%d %b %Y %I:%M %p IST')}"
                if delivered_aware
                else "Delivered."
            )
        elif order.status == "Cancelled":
            eta_str = "Order was cancelled. Refund/void processed."
        elif order.status in ("Refund Pending Approval", "Refunded"):
            eta_str = f"Order status: {order.status}."
        elif order.status == "Exchanged":
            eta_str = "Exchange dispatched. Check new tracking for delivery."
        items = [
            {
                "product_name": it.product_name,
                "sku": it.sku,
                "size": it.size,
                "quantity": it.quantity,
                "price_inr": it.unit_price_inr,
            }
            for it in order.items
        ]

        return json.dumps({
            "order_number": order.order_number,
            "status": order.status,
            "carrier": order.carrier or "Not yet assigned",
            "tracking_number": order.tracking_number or "Not yet assigned",
            "eta": eta_str,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "total_amount_inr": order.total_amount_inr,
            "total_formatted": f"₹{order.total_amount_inr:,.0f}",
            "shipping_address": order.shipping_address,
            "placed_on": order.created_at.strftime("%d %b %Y") if order.created_at else "N/A",
            "items": items,
        }, indent=2)


@tool
def cancel_or_modify_order(
    order_number: str,
    action: str,
    new_address: Optional[str] = None,
) -> str:
    """
    Cancel an order or modify its shipping address.

    CANCELLATION RULES (strictly enforced):
    - Allowed only when status is 'Processing' or 'Packed'.
    - Cancelling restores the item stock back into the product inventory.
    - Status 'In Transit' or 'Delivered' → refuse cancellation, suggest return.

    ADDRESS MODIFICATION RULES:
    - Allowed only when status is 'Processing' or 'Packed'.
    - Provide the full new address in new_address.

    Args:
        order_number: The AETHER order number, e.g. 'AETH-1001'.
        action:       One of: 'cancel', 'modify_address'
        new_address:  Required if action is 'modify_address'. Full new address string.

    Returns:
        JSON result of the operation, or an error if the action is not permitted.
    """
    action = action.lower().strip()
    order_number = order_number.upper().strip()

    with _db() as db:
        order = db.query(Order).filter_by(order_number=order_number).first()

        if not order:
            return json.dumps({"error": f"Order '{order_number}' not found."})

        cancellable_statuses = ("Processing", "Packed")
        blocked_statuses = ("In Transit", "Out for Delivery", "Delivered")

        # ── CANCEL ─────────────────────────────────────────────────────────────
        if action == "cancel":
            if order.status in blocked_statuses:
                return json.dumps({
                    "error": (
                        f"Order {order_number} cannot be cancelled — "
                        f"it is currently '{order.status}'. "
                        f"Please wait for delivery and then initiate a return. "
                        f"I can help you with a refund or exchange after delivery."
                    ),
                    "current_status": order.status,
                    "suggest_return": True,
                })

            if order.status in ("Cancelled", "Refunded", "Refund Pending Approval"):
                return json.dumps({
                    "error": f"Order {order_number} is already in '{order.status}' state."
                })

            if order.status not in cancellable_statuses:
                return json.dumps({
                    "error": (
                        f"Order {order_number} has status '{order.status}' "
                        f"which does not support cancellation."
                    )
                })

            # Restore stock for each item in the order
            for item in order.items:
                product = db.query(Product).filter_by(id=item.product_id).first()
                if product:
                    product.increment_stock(item.size, item.quantity)

            order.status = "Cancelled"
            order.updated_at = _now()

            # Initiate void / refund based on payment method
            refund_note = ""
            if order.payment_method in ("UPI", "Card"):
                order.payment_status = "Refunded"
                refund_note = (
                    f"Refund of ₹{order.total_amount_inr:,.0f} will be "
                    f"credited to your {order.payment_method} within 3–5 business days."
                )
            elif order.payment_method == "COD":
                refund_note = "COD order — no payment was collected. Order voided."

            return json.dumps({
                "success": True,
                "order_number": order_number,
                "new_status": "Cancelled",
                "refund_note": refund_note,
                "message": (
                    f"Order {order_number} has been successfully cancelled. "
                    f"{refund_note}"
                ),
                "requires_notification": True,
            }, indent=2)

        # ── MODIFY ADDRESS ──────────────────────────────────────────────────────
        elif action == "modify_address":
            if order.status in blocked_statuses:
                return json.dumps({
                    "error": (
                        f"Address cannot be changed — order {order_number} is "
                        f"already '{order.status}'. "
                        f"Please contact the carrier ({order.carrier}) directly "
                        f"with tracking number {order.tracking_number}."
                    ),
                    "carrier": order.carrier,
                    "tracking_number": order.tracking_number,
                })

            if order.status not in cancellable_statuses:
                return json.dumps({
                    "error": (
                        f"Address modification not allowed for order status "
                        f"'{order.status}'."
                    )
                })

            if not new_address or not new_address.strip():
                return json.dumps({"error": "new_address must be provided for modify_address action."})

            old_address = order.shipping_address
            order.shipping_address = new_address.strip()
            order.updated_at = _now()

            return json.dumps({
                "success": True,
                "order_number": order_number,
                "old_address": old_address,
                "new_address": new_address.strip(),
                "message": (
                    f"Shipping address for order {order_number} has been updated. "
                    f"New address: {new_address.strip()}"
                ),
                "requires_notification": True,
            }, indent=2)

        else:
            return json.dumps({
                "error": f"Unknown action '{action}'. Use 'cancel' or 'modify_address'."
            })


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 3 TOOLS — RefundAndPaymentAgent
# ─────────────────────────────────────────────────────────────────────────────

@tool
def check_payment_and_refund_status(order_number: str) -> str:
    """
    Retrieve the payment status, transaction ID, and refund progression for an order.

    Use this tool before processing a refund or exchange to verify the payment
    state and confirm the refund amount.

    Args:
        order_number: The AETHER order number, e.g. 'AETH-1002'.

    Returns:
        JSON with payment method, transaction ID, payment status, order total,
        and current refund/order status.
    """
    with _db() as db:
        order = db.query(Order).filter_by(order_number=order_number.upper().strip()).first()

        if not order:
            return json.dumps({"error": f"Order '{order_number}' not found."})

        # Check existing approval requests (HITL tickets) for this order
        approval = (
            db.query(ApprovalRequest)
            .filter_by(order_number=order.order_number)
            .order_by(ApprovalRequest.created_at.desc())
            .first()
        )

        approval_info = None
        if approval:
            approval_info = {
                "ticket_id": approval.id,
                "action_type": approval.action_type,
                "amount_inr": approval.amount_inr,
                "status": approval.status,
                "created_at": approval.created_at.isoformat() if approval.created_at else None,
            }

        items = [
            {
                "product_name": it.product_name,
                "sku": it.sku,
                "size": it.size,
                "unit_price_inr": it.unit_price_inr,
                "quantity": it.quantity,
            }
            for it in order.items
        ]

        # Compute days since delivery (for 14-day return window check)
        days_since_delivery = None
        within_return_window = False
        if order.delivered_at:
            delivered_aware = _make_aware(order.delivered_at)
            days_since_delivery = (_now() - delivered_aware).days
            within_return_window = days_since_delivery <= 14

        return json.dumps({
            "order_number": order.order_number,
            "order_status": order.status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "transaction_id": order.transaction_id or "N/A",
            "total_amount_inr": order.total_amount_inr,
            "total_formatted": f"₹{order.total_amount_inr:,.0f}",
            "auto_refund_threshold_inr": AUTO_REFUND_THRESHOLD_INR,
            "eligible_for_auto_refund": order.total_amount_inr <= AUTO_REFUND_THRESHOLD_INR,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "days_since_delivery": days_since_delivery,
            "within_14_day_return_window": within_return_window,
            "existing_approval_ticket": approval_info,
            "items": items,
        }, indent=2)


@tool
def process_refund_or_exchange(
    order_number: str,
    item_sku: str,
    action_type: str,
    reason: str,
    target_size: Optional[str] = None,
) -> str:
    """
    Process a refund request or size exchange for a delivered order.

    REFUND LOGIC (₹5,000 threshold):
    - If total_amount_inr <= ₹5,000 AND order is Delivered AND within 14-day window:
        → AUTO-APPROVE: set order status to 'Refunded', payment_status to 'Refunded',
          and signal Agent 4 to send the customer a notification.
    - If total_amount_inr > ₹5,000:
        → ESCALATE TO HUMAN ADMIN: set order status to 'Refund Pending Approval',
          create an ApprovalRequest (PENDING_ADMIN), and signal Agent 4 to
          notify the customer of the escalation.

    SIZE EXCHANGE LOGIC:
    - Verifies target_size stock, decrements inventory, generates RMA-XXXX label,
      sets order status to 'Exchanged', and signals Agent 4 for notification.

    Args:
        order_number: The AETHER order number, e.g. 'AETH-1002'.
        item_sku:     SKU of the item being returned/exchanged.
        action_type:  One of: 'REFUND', 'EXCHANGE'
        reason:       Customer's stated reason for the refund or exchange.
        target_size:  Required for EXCHANGE — the new size requested (S/M/L/XL).

    Returns:
        JSON result including approval status, RMA label (for exchange),
        and a handoff signal for Agent 4.
    """
    action_type = action_type.upper().strip()
    order_number = order_number.upper().strip()

    if action_type not in ("REFUND", "EXCHANGE"):
        return json.dumps({
            "error": f"action_type must be 'REFUND' or 'EXCHANGE', got '{action_type}'."
        })

    with _db() as db:
        order = db.query(Order).filter_by(order_number=order_number).first()
        if not order:
            return json.dumps({"error": f"Order '{order_number}' not found."})

        # Verify the SKU exists in this order
        order_item = next(
            (it for it in order.items if it.sku == item_sku), None
        )
        if not order_item:
            valid_skus = [it.sku for it in order.items]
            return json.dumps({
                "error": (
                    f"SKU '{item_sku}' not found in order {order_number}. "
                    f"Valid SKUs for this order: {valid_skus}"
                )
            })

        # Only Delivered orders can be refunded/exchanged
        if order.status not in ("Delivered", "Exchanged"):
            if order.status in ("Refund Pending Approval", "Refunded"):
                return json.dumps({
                    "error": (
                        f"Order {order_number} already has status '{order.status}'. "
                        f"No further action needed."
                    )
                })
            return json.dumps({
                "error": (
                    f"Order {order_number} has status '{order.status}'. "
                    f"Refunds and exchanges are only available for Delivered orders."
                )
            })

        # Check 14-day return window
        if order.delivered_at:
            delivered_at_aware = _make_aware(order.delivered_at)
            days_since = (_now() - delivered_at_aware).days
            if days_since > 14:
                return json.dumps({
                    "error": (
                        f"The 14-day return window for order {order_number} has expired. "
                        f"This order was delivered {days_since} days ago. "
                        f"AETHER India's return policy allows returns within 14 days of delivery."
                    ),
                    "days_since_delivery": days_since,
                })

        # ── REFUND ─────────────────────────────────────────────────────────────
        if action_type == "REFUND":
            refund_amount = order.total_amount_inr

            if refund_amount <= AUTO_REFUND_THRESHOLD_INR:
                # TIER 1: Auto-approve refund
                order.status = "Refunded"
                order.payment_status = "Refunded"
                order.updated_at = _now()

                return json.dumps({
                    "success": True,
                    "result": "AUTO_APPROVED",
                    "order_number": order_number,
                    "refund_amount_inr": refund_amount,
                    "refund_amount_formatted": f"₹{refund_amount:,.0f}",
                    "payment_method": order.payment_method,
                    "refund_timeline": (
                        "3–5 business days to your UPI ID"
                        if order.payment_method == "UPI"
                        else "5–7 business days to your card/bank"
                        if order.payment_method == "Card"
                        else "5–7 business days via NEFT bank transfer"
                    ),
                    "new_order_status": "Refunded",
                    "reason": reason,
                    "message": (
                        f"Refund of ₹{refund_amount:,.0f} for order {order_number} "
                        f"has been automatically approved and initiated. "
                        f"You will receive the credit in 3–7 business days."
                    ),
                    "requires_notification": True,
                    "notification_type": "REFUND_PROCESSED",
                    "notification_title": f"Refund Approved — {order_number}",
                    "notification_message": (
                        f"Your refund of ₹{refund_amount:,.0f} for order {order_number} "
                        f"has been approved and initiated. "
                        f"Credit expected within 3–7 business days."
                    ),
                    "user_id": order.user_id,
                    "handoff_to_agent4": True,
                    "agent4_task": "SEND_NOTIFICATION",
                }, indent=2)

            else:
                # TIER 2: Escalate to human admin (> ₹5,000)
                order.status = "Refund Pending Approval"
                order.updated_at = _now()

                ai_summary = (
                    f"Customer {order.user.name if order.user else f'ID {order.user_id}'} "
                    f"is requesting a refund of ₹{refund_amount:,.0f} for order {order_number} "
                    f"({order_item.product_name}, Size {order_item.size}). "
                    f"Reason: {reason}. "
                    f"Order was delivered {((_now() - _make_aware(order.delivered_at)).days if order.delivered_at else 'N/A')} days ago. "
                    f"Payment: {order.payment_method} (TXN: {order.transaction_id or 'N/A'}). "
                    f"Amount exceeds ₹{AUTO_REFUND_THRESHOLD_INR:,.0f} auto-approval threshold. "
                    f"Escalating for human authorization."
                )

                approval = ApprovalRequest(
                    order_id=order.id,
                    order_number=order_number,
                    user_id=order.user_id,
                    action_type="HIGH_VALUE_REFUND",
                    amount_inr=refund_amount,
                    reason=reason,
                    ai_summary=ai_summary,
                    status="PENDING_ADMIN",
                    created_at=_now(),
                )
                db.add(approval)
                db.flush()

                return json.dumps({
                    "success": True,
                    "result": "ESCALATED_TO_ADMIN",
                    "order_number": order_number,
                    "refund_amount_inr": refund_amount,
                    "refund_amount_formatted": f"₹{refund_amount:,.0f}",
                    "approval_request_id": approval.id,
                    "threshold_inr": AUTO_REFUND_THRESHOLD_INR,
                    "reason": reason,
                    "new_order_status": "Refund Pending Approval",
                    "message": (
                        f"Your refund request of ₹{refund_amount:,.0f} for order {order_number} "
                        f"exceeds the ₹{AUTO_REFUND_THRESHOLD_INR:,.0f} auto-approval limit. "
                        f"It has been escalated to our operations team. "
                        f"You will receive a decision within 24–48 hours."
                    ),
                    "requires_notification": True,
                    "notification_type": "ESCALATION_LOGGED",
                    "notification_title": f"Refund Under Review — {order_number}",
                    "notification_message": (
                        f"Your refund request of ₹{refund_amount:,.0f} for order "
                        f"{order_number} has been escalated to our operations team. "
                        f"Decision expected within 24–48 hours."
                    ),
                    "user_id": order.user_id,
                    "handoff_to_agent4": True,
                    "agent4_task": "ESCALATE",
                    "ai_summary": ai_summary,
                }, indent=2)

        # ── EXCHANGE ───────────────────────────────────────────────────────────
        elif action_type == "EXCHANGE":
            if not target_size:
                return json.dumps({
                    "error": "target_size is required for an exchange. "
                             "Please specify the new size: S, M, L, or XL."
                })

            target_size = target_size.upper().strip()

            # Find the product to check target size stock
            product = db.query(Product).filter_by(id=order_item.product_id).first()
            if not product:
                # Try by SKU
                product = db.query(Product).filter_by(sku=item_sku).first()

            if not product:
                return json.dumps({
                    "error": f"Product for SKU '{item_sku}' not found in catalog."
                })

            # Check target size stock
            target_stock = product.get_stock_for_size(target_size)
            if target_stock < order_item.quantity:
                available_sizes = [s for s, q in product.sizes.items() if q >= order_item.quantity]
                return json.dumps({
                    "error": (
                        f"Size {target_size} is out of stock for {product.name}. "
                        f"Available sizes with sufficient stock: "
                        f"{available_sizes or 'None — item is sold out in all sizes'}. "
                        f"I can process a full refund instead if you prefer."
                    ),
                    "can_exchange": False,
                    "suggest_refund": True,
                })

            # Decrement target size stock
            product.decrement_stock(target_size, order_item.quantity)

            # Generate RMA label
            rma_number = _generate_rma_number(db)

            # Update order status
            order.status = "Exchanged"
            order.updated_at = _now()

            return json.dumps({
                "success": True,
                "result": "EXCHANGE_APPROVED",
                "order_number": order_number,
                "product_name": product.name,
                "original_size": order_item.size,
                "new_size": target_size,
                "quantity": order_item.quantity,
                "rma_label": rma_number,
                "rma_valid_days": 7,
                "new_order_status": "Exchanged",
                "reason": reason,
                "message": (
                    f"Exchange approved for order {order_number}! "
                    f"Your {product.name} will be exchanged from size "
                    f"{order_item.size} to size {target_size}. "
                    f"RMA label: {rma_number} (valid for 7 days). "
                    f"Initiate your return pickup with the label — "
                    f"replacement ships within 2–3 business days of receiving your return."
                ),
                "requires_notification": True,
                "notification_type": "EXCHANGE_APPROVED",
                "notification_title": f"Exchange Approved — {order_number}",
                "notification_message": (
                    f"Your size exchange from {order_item.size} to {target_size} "
                    f"for order {order_number} is approved! "
                    f"Use RMA label {rma_number} to return your item. "
                    f"Replacement ships within 2–3 business days."
                ),
                "user_id": order.user_id,
                "handoff_to_agent4": True,
                "agent4_task": "SEND_NOTIFICATION",
            }, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 4 TOOLS — NotificationAndEscalationAgent
# ─────────────────────────────────────────────────────────────────────────────

@tool
def send_customer_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
) -> str:
    """
    Send a real-time in-app notification to a customer.

    This writes a record to the Notification table which appears in the
    customer's notification bell drawer. Valid notification_type values:
    ORDER_CONFIRMED, REFUND_PROCESSED, EXCHANGE_APPROVED, ESCALATION_LOGGED,
    CANCELLATION_CONFIRMED, ORDER_SHIPPED, GENERAL

    Args:
        user_id:           The customer's user ID.
        title:             Short notification title (max ~80 chars).
        message:           Full notification message text.
        notification_type: Category from the list above.

    Returns:
        JSON confirming the notification was written to the database.
    """
    valid_types = {
        "ORDER_CONFIRMED", "REFUND_PROCESSED", "EXCHANGE_APPROVED",
        "ESCALATION_LOGGED", "CANCELLATION_CONFIRMED", "ORDER_SHIPPED", "GENERAL",
    }
    notif_type = notification_type.upper().strip()
    if notif_type not in valid_types:
        notif_type = "GENERAL"

    with _db() as db:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return json.dumps({"error": f"User ID {user_id} not found."})

        notification = Notification(
            user_id=user_id,
            title=title[:128],
            message=message,
            notification_type=notif_type,
            is_read=False,
            created_at=_now(),
        )
        db.add(notification)
        db.flush()

        return json.dumps({
            "success": True,
            "notification_id": notification.id,
            "user_id": user_id,
            "user_name": user.name,
            "title": title,
            "notification_type": notif_type,
            "message": f"Notification sent to {user.name}: '{title}'",
        }, indent=2)


@tool
def escalate_to_human_admin(
    order_number: str,
    user_id: int,
    action_type: str,
    amount_inr: float,
    reason: str,
    ai_summary: str,
) -> str:
    """
    Create a Human-in-the-Loop (HITL) approval ticket in the Admin Dashboard
    and notify the customer that their request is under review.

    This is called automatically by process_refund_or_exchange when a refund
    exceeds ₹5,000, or when a policy dispute requires human review.

    Args:
        order_number: The AETHER order number, e.g. 'AETH-1003'.
        user_id:      The customer's user ID.
        action_type:  'HIGH_VALUE_REFUND' or 'POLICY_EXCEPTION'.
        amount_inr:   The rupee amount under review.
        reason:       Customer's stated reason.
        ai_summary:   AI-generated case summary for the admin reviewer.

    Returns:
        JSON with the new ApprovalRequest ID and a confirmation that the
        customer was also notified.
    """
    action_type = action_type.upper().strip()
    if action_type not in ("HIGH_VALUE_REFUND", "POLICY_EXCEPTION"):
        action_type = "HIGH_VALUE_REFUND"

    with _db() as db:
        order = db.query(Order).filter_by(order_number=order_number.upper().strip()).first()
        if not order:
            return json.dumps({"error": f"Order '{order_number}' not found."})

        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return json.dumps({"error": f"User ID {user_id} not found."})

        # Check if an approval ticket already exists for this order
        existing = (
            db.query(ApprovalRequest)
            .filter_by(order_number=order_number.upper(), status="PENDING_ADMIN")
            .first()
        )
        if existing:
            # Notify the customer anyway
            notification = Notification(
                user_id=user_id,
                title=f"Refund Request Under Review — {order_number}",
                message=(
                    f"Your refund request of ₹{amount_inr:,.0f} for order "
                    f"{order_number} is already under review (Ticket #{existing.id}). "
                    f"Our team will respond within 24–48 hours."
                ),
                notification_type="ESCALATION_LOGGED",
                is_read=False,
                created_at=_now(),
            )
            db.add(notification)

            return json.dumps({
                "success": True,
                "existing_ticket_id": existing.id,
                "message": (
                    f"An approval ticket (#{existing.id}) already exists for order "
                    f"{order_number}. Customer notified."
                ),
            }, indent=2)

        # Create new ApprovalRequest
        approval = ApprovalRequest(
            order_id=order.id,
            order_number=order_number.upper(),
            user_id=user_id,
            action_type=action_type,
            amount_inr=amount_inr,
            reason=reason,
            ai_summary=ai_summary,
            status="PENDING_ADMIN",
            created_at=_now(),
        )
        db.add(approval)
        db.flush()

        # Notify the customer about the escalation
        notification = Notification(
            user_id=user_id,
            title=f"Your Refund is Under Review — {order_number}",
            message=(
                f"Your refund request of ₹{amount_inr:,.0f} for order {order_number} "
                f"has been escalated to our operations team for approval (Ticket #{approval.id}). "
                f"Reason: {reason[:120]}. "
                f"We will update you within 24–48 hours."
            ),
            notification_type="ESCALATION_LOGGED",
            is_read=False,
            created_at=_now(),
        )
        db.add(notification)

        return json.dumps({
            "success": True,
            "approval_request_id": approval.id,
            "order_number": order_number,
            "action_type": action_type,
            "amount_inr": amount_inr,
            "amount_formatted": f"₹{amount_inr:,.0f}",
            "status": "PENDING_ADMIN",
            "customer_notified": True,
            "message": (
                f"Escalation ticket #{approval.id} created for order {order_number}. "
                f"Admin review required for ₹{amount_inr:,.0f} refund. "
                f"Customer {user.name} has been notified."
            ),
        }, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Tool lists for each agent (imported by agent.py)
# ─────────────────────────────────────────────────────────────────────────────

AGENT1_TOOLS = [query_brand_knowledge_rag, search_and_style_products]

AGENT2_TOOLS = [
    create_new_order,
    check_inventory_and_add_to_cart,
    check_order_status,
    cancel_or_modify_order,
]

AGENT3_TOOLS = [check_payment_and_refund_status, process_refund_or_exchange]

AGENT4_TOOLS = [send_customer_notification, escalate_to_human_admin]

ALL_TOOLS = AGENT1_TOOLS + AGENT2_TOOLS + AGENT3_TOOLS + AGENT4_TOOLS
