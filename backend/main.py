"""
main.py — FastAPI Application for AETHER INDIA.

Luxury Streetwear & Apparel E-Commerce Platform powered by
a 4-Agent LangGraph Multi-Agent System.

Endpoints:
  Auth:
    POST /api/auth/login
    GET  /api/auth/me
  Products:
    GET  /api/products
    GET  /api/products/{id_or_sku}
  Orders (Customer Storefront & Checkout):
    POST /api/orders
    GET  /api/orders
    GET  /api/orders/{order_number}
    POST /api/orders/{order_number}/cancel
  Multi-Agent Chat:
    POST /api/chat
  Notifications:
    GET  /api/notifications
    POST /api/notifications/{notification_id}/read
    POST /api/notifications/read-all
  Admin Operations Dashboard (Role: admin):
    GET   /api/admin/kpis
    GET   /api/admin/orders
    PATCH /api/admin/orders/{order_number}/status
    GET   /api/admin/inventory
    PATCH /api/admin/inventory/{product_id}
    GET   /api/admin/approvals
    POST  /api/admin/approvals/{approval_id}/action
    GET   /api/admin/agent-logs
"""
from __future__ import annotations

import json
import os
import random
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

# ── Ensure project root is in sys.path ─────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

load_dotenv()

from db.database import get_db, init_db
from db.models import (
    AgentActionLog,
    ApprovalRequest,
    Notification,
    Order,
    OrderItem,
    Product,
    User,
)
from api.auth import (
    create_access_token,
    get_current_admin,
    get_current_user,
    get_optional_user,
    verify_password,
)
from api.schemas import (
    AdminApprovalActionRequest,
    AdminKPISummaryResponse,
    AgentActionLogResponse,
    ApprovalRequestResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    LoginRequest,
    NotificationReadResponse,
    NotificationResponse,
    OrderCancelRequest,
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
    ProductResponse,
    ProductStockUpdateRequest,
    TokenResponse,
    ToolTraceItem,
    UserResponse,
)
from agents.agent import run_agent
from agents.tools import _carrier_for_address, _eta_days_for_carrier, _generate_order_number, _generate_tracking_number, _generate_transaction_id


# ─────────────────────────────────────────────────────────────────────────────
# Application Lifecycle & Initialization
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap database tables on server startup."""
    init_db()
    print("[AETHER INDIA] Database initialized successfully.")
    yield
    print("[AETHER INDIA] Server shutting down.")


app = FastAPI(
    title="AETHER INDIA API",
    description="Luxury Streetwear Operations API powered by a 4-Agent LangGraph Multi-Agent System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _format_product(p: Product) -> ProductResponse:
    """Format SQLAlchemy Product into Pydantic ProductResponse."""
    return ProductResponse(
        id=p.id,
        sku=p.sku,
        name=p.name,
        category=p.category,
        price_inr=p.price_inr,
        price_formatted=f"₹{p.price_inr:,.0f}",
        sizes=p.sizes,
        fit_type=p.fit_type,
        fabric_gsm=p.fabric_gsm,
        style_tags=p.style_tags,
        image_url=p.image_url,
        description=p.description,
        is_active=p.is_active,
        total_stock=p.total_stock,
    )


def _format_order(o: Order) -> OrderResponse:
    """Format SQLAlchemy Order into Pydantic OrderResponse."""
    items_response = [
        OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            sku=item.sku,
            size=item.size,
            quantity=item.quantity,
            unit_price_inr=item.unit_price_inr,
            subtotal_inr=item.subtotal_inr,
        )
        for item in o.items
    ]
    return OrderResponse(
        id=o.id,
        order_number=o.order_number,
        user_id=o.user_id,
        status=o.status,
        total_amount_inr=o.total_amount_inr,
        total_formatted=f"₹{o.total_amount_inr:,.0f}",
        payment_method=o.payment_method,
        payment_status=o.payment_status,
        transaction_id=o.transaction_id,
        shipping_address=o.shipping_address,
        tracking_number=o.tracking_number,
        carrier=o.carrier,
        created_at=o.created_at,
        delivered_at=o.delivered_at,
        items=items_response,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Authentication Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate customer or admin user.
    Demo credentials:
      - Customer: aarav@customer.com / Demo@1234
      - Admin:    admin@aether.in    / Demo@1234
    """
    user = db.query(User).filter(User.email == payload.email.lower().strip(), User.is_active == True).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
def get_profile(current_user: User = Depends(get_current_user)):
    """Fetch current authenticated user profile."""
    return UserResponse.model_validate(current_user)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Product Catalog Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/products", response_model=List[ProductResponse], tags=["Catalog"])
def list_products(
    category: Optional[str] = Query(None, description="Category filter (Hoodies, Tees, Bottoms, Outerwear, Accessories)"),
    search: Optional[str] = Query(None, description="Search term for name, description, or style tags"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    size: Optional[str] = Query(None, pattern="^(S|M|L|XL|s|m|l|xl)$"),
    in_stock_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Browse catalog with filters for category, price, size, and search keywords."""
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if min_price is not None:
        query = query.filter(Product.price_inr >= min_price)
    if max_price is not None:
        query = query.filter(Product.price_inr <= max_price)

    products = query.all()

    # Search filter across multiple text columns
    if search:
        search_terms = search.lower().split()
        filtered = []
        for p in products:
            blob = f"{p.name} {p.description or ''} {p.style_tags or ''} {p.category}".lower()
            if any(term in blob for term in search_terms):
                filtered.append(p)
        products = filtered

    # Size & in-stock filters
    if size:
        size_upper = size.upper()
        products = [p for p in products if p.get_stock_for_size(size_upper) > 0]
    elif in_stock_only:
        products = [p for p in products if p.total_stock > 0]

    return [_format_product(p) for p in products]


@app.get("/api/products/{id_or_sku}", response_model=ProductResponse, tags=["Catalog"])
def get_product(id_or_sku: str, db: Session = Depends(get_db)):
    """Fetch product details by numerical ID or SKU."""
    if id_or_sku.isdigit():
        product = db.query(Product).filter(Product.id == int(id_or_sku), Product.is_active == True).first()
    else:
        product = db.query(Product).filter(Product.sku == id_or_sku.upper().strip(), Product.is_active == True).first()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{id_or_sku}' not found")
    return _format_product(product)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Order & Checkout Endpoints (Customer Storefront)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new order from UI Cart Checkout:
      - Validates stock per item & size in `Product.sizes_json`
      - Decrements inventory atomically
      - Generates order number `AETH-XXXX`
      - Assigns logistics carrier (BlueDart / Delhivery) based on city
      - Creates `Order` and `OrderItem` records
      - Triggers an in-app `ORDER_CONFIRMED` notification
    """
    total_amount = 0.0
    items_to_create = []

    # 1. Validation & Stock Reservation Check
    for item_req in payload.items:
        size_key = item_req.size.upper()
        product = db.query(Product).filter(Product.id == item_req.product_id, Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item_req.product_id} not found")

        available_stock = product.get_stock_for_size(size_key)
        if available_stock < item_req.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name} (Size {size_key}). Requested: {item_req.quantity}, Available: {available_stock}",
            )

        item_subtotal = product.price_inr * item_req.quantity
        total_amount += item_subtotal
        items_to_create.append({
            "product": product,
            "size": size_key,
            "quantity": item_req.quantity,
            "unit_price": product.price_inr,
        })

    # 2. Logistics & Payment Details
    order_number = _generate_order_number(db)
    carrier = _carrier_for_address(payload.shipping_address)
    tracking_number = _generate_tracking_number(carrier)

    pm = payload.payment_method.strip()
    if pm in ("UPI", "Card", "Credit/Debit Card"):
        payment_status = "Paid"
        transaction_id = _generate_transaction_id("UPI" if pm == "UPI" else "CARD")
    else:
        payment_status = "Pending"
        transaction_id = None

    # 3. Create Order
    new_order = Order(
        order_number=order_number,
        user_id=current_user.id,
        status="Processing",
        total_amount_inr=total_amount,
        payment_method="Card" if "Card" in pm else pm,
        payment_status=payment_status,
        transaction_id=transaction_id,
        shipping_address=payload.shipping_address,
        tracking_number=tracking_number,
        carrier=carrier,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_order)
    db.flush()

    # 4. Create OrderItems & Decrement Stock
    for it in items_to_create:
        prod = it["product"]
        size_key = it["size"]
        qty = it["quantity"]

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=prod.id,
            product_name=prod.name,
            sku=prod.sku,
            size=size_key,
            quantity=qty,
            unit_price_inr=it["unit_price"],
        )
        db.add(order_item)
        prod.decrement_stock(size_key, qty)

    # 5. Emit In-App Notification
    eta = _eta_days_for_carrier(carrier, payload.shipping_address)
    notification = Notification(
        user_id=current_user.id,
        title=f"Order Confirmed — {order_number} 🛍️",
        message=f"Thank you! Your order {order_number} worth ₹{total_amount:,.0f} has been placed. Shipping via {carrier} (ETA: {eta}).",
        notification_type="ORDER_CONFIRMED",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    db.commit()
    db.refresh(new_order)

    return _format_order(new_order)


@app.get("/api/orders", response_model=List[OrderResponse], tags=["Orders"])
def list_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all orders placed by the current authenticated user."""
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(desc(Order.created_at)).all()
    return [_format_order(o) for o in orders]


@app.get("/api/orders/{order_number}", response_model=OrderResponse, tags=["Orders"])
def get_order_detail(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch order details and live delivery status for a specific order."""
    order = db.query(Order).filter(Order.order_number == order_number.upper().strip()).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_number}' not found")

    # Authorisation check: customer can only view their own order; admin can view all
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this order")

    return _format_order(order)


@app.post("/api/orders/{order_number}/cancel", response_model=OrderResponse, tags=["Orders"])
def cancel_order(
    order_number: str,
    payload: OrderCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel an order:
      - Allowed only if status is 'Processing' or 'Packed'
      - Automatically restores stock for all item sizes back to `Product.sizes_json`
      - Updates order and payment statuses
      - Dispatches a cancellation notification
    """
    order = db.query(Order).filter(Order.order_number == order_number.upper().strip()).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_number}' not found")

    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to cancel this order")

    if order.status in ("In Transit", "Delivered"):
        raise HTTPException(
            status_code=400,
            detail=f"Order {order_number} is already '{order.status}'. Cancellation not permitted. Please initiate a return once delivered.",
        )
    if order.status in ("Cancelled", "Refunded"):
        raise HTTPException(status_code=400, detail=f"Order is already '{order.status}'")

    # Restore inventory
    for item in order.items:
        if item.product:
            item.product.increment_stock(item.size, item.quantity)

    order.status = "Cancelled"
    if order.payment_method in ("UPI", "Card"):
        order.payment_status = "Refunded"
    order.updated_at = datetime.now(timezone.utc)

    # Dispatched notification
    notif = Notification(
        user_id=order.user_id,
        title=f"Order Cancelled — {order.order_number}",
        message=f"Order {order.order_number} has been cancelled. Any pre-paid amount (₹{order.total_amount_inr:,.0f}) will be refunded in 3–5 days.",
        notification_type="CANCELLATION_CONFIRMED",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(notif)
    db.commit()
    db.refresh(order)

    return _format_order(order)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Multi-Agent Chat Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatMessageResponse, tags=["Multi-Agent Chat"])
def chat_with_multi_agent(
    payload: ChatMessageRequest,
    optional_user: Optional[User] = Depends(get_optional_user),
):
    """
    Process user query through the LangGraph Supervisor Multi-Agent System:
      - Supervisor routes between 4 specialized agents
      - Returns agent response, active agent badge, and tool trace logs
    """
    user_id = optional_user.id if optional_user else None

    # Execute LangGraph
    agent_result = run_agent(
        message=payload.message,
        user_id=user_id,
        session_id=payload.session_id,
    )

    result_dict = agent_result.to_dict()

    trace_items = [
        ToolTraceItem(
            agent=entry.get("agent"),
            tool=entry.get("tool"),
            input_summary=entry.get("input_summary"),
            output_summary=entry.get("output_summary"),
            timestamp=entry.get("timestamp"),
        )
        for entry in result_dict.get("tool_trace", [])
    ]

    return ChatMessageResponse(
        response=result_dict.get("response", ""),
        routed_agent=result_dict.get("routed_agent"),
        trace_badge=result_dict.get("trace_badge", "Supervisor"),
        tool_trace=trace_items,
        session_id=result_dict.get("session_id", ""),
        error=result_dict.get("error"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Customer Notification Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/notifications", response_model=List[NotificationResponse], tags=["Notifications"])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all notifications for the authenticated customer."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .all()
    )
    return notifications


@app.post("/api/notifications/{notification_id}/read", response_model=NotificationReadResponse, tags=["Notifications"])
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()

    unread = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).count()
    return NotificationReadResponse(success=True, unread_count=unread)


@app.post("/api/notifications/read-all", response_model=NotificationReadResponse, tags=["Notifications"])
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications for the user as read."""
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return NotificationReadResponse(success=True, unread_count=0)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Admin Operations Dashboard Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/kpis", response_model=AdminKPISummaryResponse, tags=["Admin Operations"])
def get_admin_kpis(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Aggregate platform KPIs for the Operations Head dashboard."""
    # Total revenue from paid/completed orders
    revenue = (
        db.query(func.sum(Order.total_amount_inr))
        .filter(Order.payment_status.in_(["Paid", "Pending"]), Order.status != "Cancelled")
        .scalar()
        or 0.0
    )

    total_orders = db.query(Order).count()
    pending_approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING_ADMIN").count()

    # AI resolved vs escalated
    escalated_count = db.query(ApprovalRequest).count()
    total_logs = db.query(AgentActionLog).count()
    auto_resolved = max(0, total_logs - escalated_count)

    active_products = db.query(Product).filter(Product.is_active == True).count()
    total_customers = db.query(User).filter(User.role == "customer").count()

    return AdminKPISummaryResponse(
        total_revenue_inr=float(revenue),
        total_revenue_formatted=f"₹{revenue:,.0f}",
        total_orders_count=total_orders,
        pending_approvals_count=pending_approvals,
        ai_auto_resolved_count=auto_resolved,
        human_escalated_count=escalated_count,
        active_products_count=active_products,
        total_customers_count=total_customers,
    )


@app.get("/api/admin/orders", response_model=List[OrderResponse], tags=["Admin Operations"])
def admin_list_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """View all platform orders with optional status filtering."""
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    orders = query.order_by(desc(Order.created_at)).all()
    return [_format_order(o) for o in orders]


@app.patch("/api/admin/orders/{order_number}/status", response_model=OrderResponse, tags=["Admin Operations"])
def admin_update_order_status(
    order_number: str,
    payload: OrderStatusUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update order shipping status and tracking carrier details."""
    order = db.query(Order).filter(Order.order_number == order_number.upper().strip()).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order '{order_number}' not found")

    old_status = order.status
    order.status = payload.status
    if payload.tracking_number:
        order.tracking_number = payload.tracking_number
    if payload.carrier:
        order.carrier = payload.carrier
    if payload.status == "Delivered" and not order.delivered_at:
        order.delivered_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)

    # Notify customer of progress
    if payload.status != old_status:
        notif = Notification(
            user_id=order.user_id,
            title=f"Order Update — {order.order_number}",
            message=f"Status update: Your order {order.order_number} is now '{payload.status}'. Carrier: {order.carrier or 'BlueDart'}.",
            notification_type="ORDER_SHIPPED" if payload.status in ("In Transit", "Packed") else "GENERAL",
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notif)

    db.commit()
    db.refresh(order)
    return _format_order(order)


@app.get("/api/admin/inventory", response_model=List[ProductResponse], tags=["Admin Operations"])
def admin_get_inventory(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get complete product catalog with live size stock levels."""
    products = db.query(Product).order_by(Product.id).all()
    return [_format_product(p) for p in products]


@app.patch("/api/admin/inventory/{product_id}", response_model=ProductResponse, tags=["Admin Operations"])
def admin_update_stock(
    product_id: int,
    payload: ProductStockUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Restock product sizes directly from the Operations Dashboard."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    current_sizes = product.sizes
    current_sizes.update({k.upper(): v for k, v in payload.sizes.items()})
    product.set_sizes(current_sizes)
    db.commit()
    db.refresh(product)
    return _format_product(product)


@app.get("/api/admin/approvals", response_model=List[ApprovalRequestResponse], tags=["Admin Operations"])
def admin_get_approvals(
    status_filter: Optional[str] = Query("PENDING_ADMIN", alias="status"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Fetch Human-in-the-Loop approval requests."""
    query = db.query(ApprovalRequest)
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(ApprovalRequest.status == status_filter.upper())
    requests = query.order_by(desc(ApprovalRequest.created_at)).all()

    return [
        ApprovalRequestResponse(
            id=req.id,
            order_id=req.order_id,
            order_number=req.order_number,
            user_id=req.user_id,
            action_type=req.action_type,
            amount_inr=req.amount_inr,
            amount_formatted=f"₹{req.amount_inr:,.0f}",
            reason=req.reason,
            ai_summary=req.ai_summary,
            status=req.status,
            admin_notes=req.admin_notes,
            created_at=req.created_at,
            resolved_at=req.resolved_at,
        )
        for req in requests
    ]


@app.post("/api/admin/approvals/{approval_id}/action", response_model=ApprovalRequestResponse, tags=["Admin Operations"])
def admin_act_on_approval(
    approval_id: int,
    payload: AdminApprovalActionRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Human-in-the-Loop decision execution:
      - Approving sets `ApprovalRequest.status = APPROVED`, `Order.status = Refunded`, and triggers refund notification.
      - Rejecting keeps `ApprovalRequest.status = REJECTED`, `Order.status = Delivered`, and triggers notification with admin notes.
    """
    req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Approval ticket not found")

    if req.status != "PENDING_ADMIN":
        raise HTTPException(status_code=400, detail=f"Ticket #{approval_id} is already '{req.status}'")

    req.status = payload.action.upper()
    req.admin_notes = payload.admin_notes
    req.resolved_at = datetime.now(timezone.utc)

    order = req.order
    if payload.action.upper() == "APPROVE":
        if order:
            order.status = "Refunded"
            order.payment_status = "Refunded"
            order.updated_at = datetime.now(timezone.utc)

        notif = Notification(
            user_id=req.user_id,
            title=f"Refund Approved by Operations — {req.order_number} ✅",
            message=f"Your refund request for ₹{req.amount_inr:,.0f} has been approved by our operations team. Credit will reflect within 3–5 business days.",
            notification_type="REFUND_PROCESSED",
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notif)
    else:
        if order:
            order.status = "Delivered"
            order.updated_at = datetime.now(timezone.utc)

        reason_note = f" Reason: {payload.admin_notes}" if payload.admin_notes else ""
        notif = Notification(
            user_id=req.user_id,
            title=f"Refund Request Update — {req.order_number}",
            message=f"Your refund request of ₹{req.amount_inr:,.0f} could not be approved at this time.{reason_note}",
            notification_type="GENERAL",
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notif)

    db.commit()
    db.refresh(req)

    return ApprovalRequestResponse(
        id=req.id,
        order_id=req.order_id,
        order_number=req.order_number,
        user_id=req.user_id,
        action_type=req.action_type,
        amount_inr=req.amount_inr,
        amount_formatted=f"₹{req.amount_inr:,.0f}",
        reason=req.reason,
        ai_summary=req.ai_summary,
        status=req.status,
        admin_notes=req.admin_notes,
        created_at=req.created_at,
        resolved_at=req.resolved_at,
    )


@app.get("/api/admin/agent-logs", response_model=List[AgentActionLogResponse], tags=["Admin Operations"])
def admin_get_agent_logs(
    limit: int = Query(50, ge=1, le=200),
    agent_filter: Optional[str] = Query(None, alias="agent"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Retrieve multi-agent audit logs for the Operations Dashboard."""
    query = db.query(AgentActionLog)
    if agent_filter:
        query = query.filter(AgentActionLog.routed_agent == agent_filter)
    logs = query.order_by(desc(AgentActionLog.created_at)).limit(limit).all()
    return logs
