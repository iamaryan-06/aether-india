const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("aether_token");
}

async function fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<any> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = "Request failed";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // ── Auth ──────────────────────────────────────────────────────────
  login: (email: string, password: string) =>
    fetchWithAuth("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getProfile: () => fetchWithAuth("/auth/me"),

  // ── Products ──────────────────────────────────────────────────────
  getProducts: (params?: { category?: string; search?: string; size?: string; max_price?: number }) => {
    const query = new URLSearchParams();
    if (params?.category) query.append("category", params.category);
    if (params?.search) query.append("search", params.search);
    if (params?.size) query.append("size", params.size);
    if (params?.max_price) query.append("max_price", params.max_price.toString());
    const qs = query.toString();
    return fetchWithAuth(`/products${qs ? `?${qs}` : ""}`);
  },

  getProduct: (idOrSku: string | number) => fetchWithAuth(`/products/${idOrSku}`),

  // ── Orders ────────────────────────────────────────────────────────
  createOrder: (payload: {
    items: { product_id: number; size: string; quantity: number }[];
    shipping_address: string;
    payment_method: string;
  }) =>
    fetchWithAuth("/orders", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getUserOrders: () => fetchWithAuth("/orders"),

  getOrderDetail: (orderNumber: string) => fetchWithAuth(`/orders/${orderNumber}`),

  cancelOrder: (orderNumber: string, reason?: string) =>
    fetchWithAuth(`/orders/${orderNumber}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  // ── Chat ──────────────────────────────────────────────────────────
  sendChatMessage: (message: string, sessionId?: string) =>
    fetchWithAuth("/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  // ── Notifications ─────────────────────────────────────────────────
  getNotifications: () => fetchWithAuth("/notifications"),

  markNotificationRead: (id: number) =>
    fetchWithAuth(`/notifications/${id}/read`, {
      method: "POST",
    }),

  markAllNotificationsRead: () =>
    fetchWithAuth("/notifications/read-all", {
      method: "POST",
    }),

  // ── Admin ─────────────────────────────────────────────────────────
  getAdminKPIs: () => fetchWithAuth("/admin/kpis"),

  getAdminOrders: (status?: string) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return fetchWithAuth(`/admin/orders${qs}`);
  },

  updateOrderStatus: (orderNumber: string, payload: { status: string; carrier?: string; tracking_number?: string }) =>
    fetchWithAuth(`/admin/orders/${orderNumber}/status`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  getAdminInventory: () => fetchWithAuth("/admin/inventory"),

  updateProductStock: (productId: number, sizes: Record<string, number>) =>
    fetchWithAuth(`/admin/inventory/${productId}`, {
      method: "PATCH",
      body: JSON.stringify({ sizes }),
    }),

  getAdminApprovals: (status = "PENDING_ADMIN") =>
    fetchWithAuth(`/admin/approvals?status=${encodeURIComponent(status)}`),

  actOnApproval: (approvalId: number, action: "APPROVE" | "REJECT", adminNotes?: string) =>
    fetchWithAuth(`/admin/approvals/${approvalId}/action`, {
      method: "POST",
      body: JSON.stringify({ action, admin_notes: adminNotes }),
    }),

  getAdminAgentLogs: (agent?: string, limit = 50) => {
    const query = new URLSearchParams({ limit: limit.toString() });
    if (agent) query.append("agent", agent);
    return fetchWithAuth(`/admin/agent-logs?${query.toString()}`);
  },
};
