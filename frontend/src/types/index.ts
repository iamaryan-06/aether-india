export interface User {
  id: number;
  name: string;
  email: string;
  role: "customer" | "admin";
  default_address?: string;
  is_active: boolean;
  created_at: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: string;
  price_inr: number;
  price_formatted?: string;
  sizes: Record<string, number>;
  fit_type?: string;
  fabric_gsm?: number;
  style_tags?: string;
  image_url?: string;
  description?: string;
  is_active: boolean;
  total_stock?: number;
}

export interface OrderItem {
  id: number;
  product_id?: number;
  product_name: string;
  sku: string;
  size: string;
  quantity: number;
  unit_price_inr: number;
  subtotal_inr?: number;
}

export interface Order {
  id: number;
  order_number: string;
  user_id: number;
  status:
    | "Processing"
    | "Packed"
    | "In Transit"
    | "Delivered"
    | "Cancelled"
    | "Exchanged"
    | "Refund Pending Approval"
    | "Refunded";
  total_amount_inr: number;
  total_formatted?: string;
  payment_method: string;
  payment_status: "Paid" | "Pending" | "Refunded";
  transaction_id?: string;
  shipping_address: string;
  tracking_number?: string;
  carrier?: "BlueDart" | "Delhivery";
  created_at: string;
  delivered_at?: string;
  items: OrderItem[];
}

export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type:
    | "ORDER_CONFIRMED"
    | "REFUND_PROCESSED"
    | "EXCHANGE_APPROVED"
    | "ESCALATION_LOGGED"
    | "CANCELLATION_CONFIRMED"
    | "ORDER_SHIPPED"
    | "GENERAL";
  is_read: boolean;
  created_at: string;
}

export interface ApprovalRequest {
  id: number;
  order_id: number;
  order_number: string;
  user_id: number;
  action_type: "HIGH_VALUE_REFUND" | "POLICY_EXCEPTION";
  amount_inr: number;
  amount_formatted?: string;
  reason: string;
  ai_summary: string;
  status: "PENDING_ADMIN" | "APPROVED" | "REJECTED";
  admin_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export interface ToolTraceItem {
  agent?: string;
  tool?: string;
  input_summary?: string;
  output_summary?: string;
  timestamp?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  routed_agent?: string;
  trace_badge?: string;
  tool_trace?: ToolTraceItem[];
  productCards?: any[];
  orderCard?: any;
  escalationCard?: any;
}

export interface CartItem {
  product: Product;
  size: string;
  quantity: number;
}

export interface AdminKPISummary {
  total_revenue_inr: number;
  total_revenue_formatted: string;
  total_orders_count: number;
  pending_approvals_count: number;
  ai_auto_resolved_count: number;
  human_escalated_count: number;
  active_products_count: number;
  total_customers_count: number;
}

export interface AgentActionLog {
  id: number;
  session_id: string;
  user_id?: number;
  user_message: string;
  routed_agent: string;
  tool_called?: string;
  tool_input?: string;
  tool_output?: string;
  final_response?: string;
  created_at: string;
}
