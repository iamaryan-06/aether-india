"""
models.py — Complete SQLAlchemy ORM models for AETHER INDIA.

Tables:
    User              — customers and admin accounts
    Product           — streetwear catalog with per-size stock (JSON)
    Order             — customer orders (AETH-XXXX numbering)
    OrderItem         — line items belonging to an Order
    ApprovalRequest   — Human-in-the-Loop (HITL) admin review tickets
    AgentActionLog    — audit log for every multi-agent tool call
    Notification      — in-app notifications (bell drawer)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _now_utc() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# 1. User
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    """
    Represents a platform user — either a customer or an admin.

    Roles:
        "customer"  — Can browse, order, and chat with the AI agents.
        "admin"     — Full access to the Admin Operations Dashboard and HITL queue.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="customer",
        comment="'customer' or 'admin'",
    )
    default_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc, nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[List["ApprovalRequest"]] = relationship(
        "ApprovalRequest", back_populates="user", cascade="all, delete-orphan"
    )
    agent_logs: Mapped[List["AgentActionLog"]] = relationship(
        "AgentActionLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Product
# ─────────────────────────────────────────────────────────────────────────────

class Product(Base):
    """
    Streetwear catalog item.

    `sizes_json` stores per-size stock as a JSON string, e.g.:
        '{"S": 5, "M": 12, "L": 0, "XL": 4}'

    Helper properties `sizes` and `set_sizes` provide dict-level access.
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="e.g. 'Hoodies', 'Tees', 'Bottoms', 'Outerwear', 'Accessories'",
    )
    price_inr: Mapped[float] = mapped_column(Float, nullable=False)
    sizes_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default='{"S": 0, "M": 0, "L": 0, "XL": 0}',
        comment="JSON object mapping size label -> stock count",
    )
    fit_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="e.g. 'Boxy', 'Oversized', 'Relaxed', 'Slim'",
    )
    fabric_gsm: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Fabric weight in GSM",
    )
    style_tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Comma-separated tags e.g. 'acid-wash,graphic,heavyweight'",
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc, nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="product"
    )

    # ── Convenience helpers for sizes_json ───────────────────────────────────

    @property
    def sizes(self) -> Dict[str, int]:
        """Return the sizes_json field as a Python dict."""
        try:
            return json.loads(self.sizes_json)
        except (json.JSONDecodeError, TypeError):
            return {"S": 0, "M": 0, "L": 0, "XL": 0}

    def set_sizes(self, sizes_dict: Dict[str, int]) -> None:
        """Serialize a dict and store it back into sizes_json."""
        self.sizes_json = json.dumps(sizes_dict)

    def get_stock_for_size(self, size: str) -> int:
        """Return stock count for a specific size key (e.g. 'M')."""
        return self.sizes.get(size.upper(), 0)

    def decrement_stock(self, size: str, quantity: int = 1) -> bool:
        """
        Decrement stock for `size` by `quantity`.
        Returns True on success, False if insufficient stock.
        """
        current = self.sizes
        size_key = size.upper()
        if current.get(size_key, 0) < quantity:
            return False
        current[size_key] -= quantity
        self.set_sizes(current)
        return True

    def increment_stock(self, size: str, quantity: int = 1) -> None:
        """Increment stock for `size` by `quantity` (used on order cancellation)."""
        current = self.sizes
        size_key = size.upper()
        current[size_key] = current.get(size_key, 0) + quantity
        self.set_sizes(current)

    @property
    def total_stock(self) -> int:
        """Return aggregate stock across all sizes."""
        return sum(self.sizes.values())

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku={self.sku!r} name={self.name!r} price=₹{self.price_inr}>"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Order
# ─────────────────────────────────────────────────────────────────────────────

class Order(Base):
    """
    A customer purchase record.

    Status lifecycle:
        Processing -> Packed -> In Transit -> Delivered
        Any status -> Cancelled   (only allowed from Processing or Packed)
        Delivered  -> Refund Pending Approval  (high-value refund > ₹5,000)
        Delivered  -> Refunded                 (auto-approved refund <= ₹5,000)
        Delivered  -> Exchanged                (size exchange)

    Payment methods: UPI | Card | COD
    Payment statuses: Paid | Pending | Refunded
    """
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, nullable=False,
        comment="Human-readable ID like AETH-1001",
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="Processing",
        comment=(
            "Processing | Packed | In Transit | Delivered | "
            "Cancelled | Exchanged | Refund Pending Approval | Refunded"
        ),
    )
    total_amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="UPI",
        comment="UPI | Card | COD",
    )
    payment_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="Paid",
        comment="Paid | Pending | Refunded",
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="BlueDart | Delhivery",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc, nullable=False
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[List["ApprovalRequest"]] = relationship(
        "ApprovalRequest", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Order id={self.id} number={self.order_number!r} "
            f"status={self.status!r} total=₹{self.total_amount_inr}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 4. OrderItem
# ─────────────────────────────────────────────────────────────────────────────

class OrderItem(Base):
    """
    A single line-item within an Order (one product / size / quantity).

    `product_name` and `sku` are denormalized so the line-item is accurate
    even if the Product record is later edited.
    """
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_name: Mapped[str] = mapped_column(String(256), nullable=False)
    sku: Mapped[str] = mapped_column(String(32), nullable=False)
    size: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_inr: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="order_items"
    )

    @property
    def subtotal_inr(self) -> float:
        return self.unit_price_inr * self.quantity

    def __repr__(self) -> str:
        return (
            f"<OrderItem id={self.id} sku={self.sku!r} "
            f"size={self.size!r} qty={self.quantity} price=₹{self.unit_price_inr}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. ApprovalRequest  (Human-in-the-Loop / HITL)
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalRequest(Base):
    """
    A Human-in-the-Loop ticket created by the NotificationAndEscalationAgent
    when a refund exceeds the ₹5,000 auto-approval threshold, or when a
    policy dispute needs human review.

    The Admin Dashboard HITL queue reads and acts on these records.

    Status flow:
        PENDING_ADMIN -> APPROVED | REJECTED
    """
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_number: Mapped[str] = mapped_column(String(16), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="HIGH_VALUE_REFUND | POLICY_EXCEPTION",
    )
    amount_inr: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Rupee amount subject to approval",
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI-generated summary of the conversation context",
    )
    status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        default="PENDING_ADMIN",
        comment="PENDING_ADMIN | APPROVED | REJECTED",
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc, nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped["Order"] = relationship("Order", back_populates="approval_requests")
    user: Mapped["User"] = relationship("User", back_populates="approval_requests")

    def __repr__(self) -> str:
        return (
            f"<ApprovalRequest id={self.id} order={self.order_number!r} "
            f"type={self.action_type!r} status={self.status!r} amount=₹{self.amount_inr}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. AgentActionLog
# ─────────────────────────────────────────────────────────────────────────────

class AgentActionLog(Base):
    """
    Immutable audit record written after every agent tool invocation.

    Used by:
        - Admin Dashboard -> Multi-Agent Routing Logs page
        - Multi-Agent Execution Trace Badge in the chat UI
    """
    __tablename__ = "agent_action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        comment="UUID identifying the browser chat session",
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    routed_agent: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment=(
            "CustomerSupportAgent | OrderAndInventoryAgent | "
            "RefundAndPaymentAgent | NotificationAndEscalationAgent"
        ),
    )
    tool_called: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tool_input: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-serialized tool arguments",
    )
    tool_output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-serialized or text tool result",
    )
    final_response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="The agent's final message sent back to the user",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc, nullable=False, index=True
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped[Optional["User"]] = relationship("User", back_populates="agent_logs")

    def __repr__(self) -> str:
        return (
            f"<AgentActionLog id={self.id} agent={self.routed_agent!r} "
            f"tool={self.tool_called!r} session={self.session_id!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. Notification
# ─────────────────────────────────────────────────────────────────────────────

class Notification(Base):
    """
    In-app notification written by the NotificationAndEscalationAgent.
    Read by the customer notification bell drawer in the frontend.

    notification_type values:
        ORDER_CONFIRMED | REFUND_PROCESSED | EXCHANGE_APPROVED |
        ESCALATION_LOGGED | CANCELLATION_CONFIRMED | ORDER_SHIPPED |
        GENERAL
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="GENERAL",
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc, nullable=False, index=True
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} user_id={self.user_id} "
            f"type={self.notification_type!r} read={self.is_read}>"
        )
