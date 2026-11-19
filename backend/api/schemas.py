"""
schemas.py — Pydantic v2 data models for AETHER INDIA REST API.

Covers:
  - Auth: LoginRequest, TokenResponse, UserResponse
  - Products: ProductResponse, ProductFilterParams, StockUpdateRequest
  - Orders: OrderItemCreate, OrderCreateRequest, OrderResponse, OrderStatusUpdateRequest, OrderCancelRequest
  - Chat: ChatMessageRequest, ToolTraceItem, ChatMessageResponse
  - Notifications: NotificationResponse, NotificationReadResponse
  - Approvals (HITL): ApprovalRequestResponse, AdminApprovalActionRequest
  - Admin KPIs & Logs: AdminKPISummaryResponse, AgentActionLogResponse
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ─────────────────────────────────────────────────────────────────────────────
# 1. Auth Schemas
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    default_address: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─────────────────────────────────────────────────────────────────────────────
# 2. Product Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    category: str
    price_inr: float
    price_formatted: Optional[str] = None
    sizes: Dict[str, int]
    fit_type: Optional[str] = None
    fabric_gsm: Optional[int] = None
    style_tags: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    total_stock: Optional[int] = None


class ProductStockUpdateRequest(BaseModel):
    sizes: Dict[str, int] = Field(
        ...,
        description="Dictionary mapping size (S, M, L, XL) to integer stock count",
        examples=[{"S": 10, "M": 15, "L": 8, "XL": 4}],
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Order Schemas
# ─────────────────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int
    size: str = Field(..., pattern="^(S|M|L|XL|s|m|l|xl)$")
    quantity: int = Field(..., ge=1, le=10)


class OrderCreateRequest(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=10)
    payment_method: str = Field(..., pattern="^(UPI|Card|COD|Credit/Debit Card)$")


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int] = None
    product_name: str
    sku: str
    size: str
    quantity: int
    unit_price_inr: float
    subtotal_inr: Optional[float] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    user_id: int
    status: str
    total_amount_inr: float
    total_formatted: Optional[str] = None
    payment_method: str
    payment_status: str
    transaction_id: Optional[str] = None
    shipping_address: str
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(Processing|Packed|In Transit|Delivered|Cancelled|Exchanged|Refund Pending Approval|Refunded)$",
    )
    tracking_number: Optional[str] = None
    carrier: Optional[str] = Field(None, pattern="^(BlueDart|Delhivery)$")


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = "Customer requested cancellation via portal"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Multi-Agent Chat Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None


class ToolTraceItem(BaseModel):
    agent: Optional[str] = None
    tool: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    timestamp: Optional[str] = None


class ChatMessageResponse(BaseModel):
    response: str
    routed_agent: Optional[str] = None
    trace_badge: str
    tool_trace: List[ToolTraceItem] = []
    session_id: str
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 5. Notification Schemas
# ─────────────────────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime


class NotificationReadResponse(BaseModel):
    success: bool
    unread_count: int


# ─────────────────────────────────────────────────────────────────────────────
# 6. Admin HITL Approval Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    order_number: str
    user_id: int
    action_type: str
    amount_inr: float
    amount_formatted: Optional[str] = None
    reason: str
    ai_summary: str
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class AdminApprovalActionRequest(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    admin_notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 7. Admin KPI & Audit Log Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AdminKPISummaryResponse(BaseModel):
    total_revenue_inr: float
    total_revenue_formatted: str
    total_orders_count: int
    pending_approvals_count: int
    ai_auto_resolved_count: int
    human_escalated_count: int
    active_products_count: int
    total_customers_count: int


class AgentActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    user_id: Optional[int] = None
    user_message: str
    routed_agent: str
    tool_called: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    final_response: Optional[str] = None
    created_at: datetime
