"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Order } from "@/types";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { formatINR } from "@/lib/utils";
import {
  Package,
  Truck,
  RotateCcw,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

const STATUS_STEPS = ["Processing", "Packed", "In Transit", "Delivered"];

function OrdersContent() {
  const searchParams = useSearchParams();
  const newOrderParam = searchParams.get("new_order");

  const [orders, setOrders] = useState<Order[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [isLoading, setIsLoading] = useState(true);
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const { isAuthenticated, loginAsDemoCustomer } = useAuthStore();

  const loadOrders = async () => {
    setIsLoading(true);
    try {
      if (!isAuthenticated) {
        await loginAsDemoCustomer();
      }
      const data = await api.getUserOrders();
      setOrders(data);
    } catch (err) {
      console.error("Failed to fetch orders", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [isAuthenticated]);

  const handleCancel = async (orderNumber: string) => {
    if (!confirm(`Are you sure you want to cancel order ${orderNumber}? Stock will be restored.`)) {
      return;
    }
    setCancellingOrder(orderNumber);
    try {
      await api.cancelOrder(orderNumber);
      setActionSuccess(`Order ${orderNumber} cancelled successfully. Stock restored.`);
      await loadOrders();
    } catch (err: any) {
      alert(`Cancellation failed: ${err.message}`);
    } finally {
      setCancellingOrder(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Delivered":
        return "bg-street-emerald/20 text-street-emerald border-street-emerald/40";
      case "In Transit":
        return "bg-street-cyan/20 text-street-cyan border-street-cyan/40";
      case "Packed":
      case "Processing":
        return "bg-street-amber/20 text-street-amber border-street-amber/40";
      case "Cancelled":
        return "bg-street-red/20 text-street-red border-street-red/40";
      case "Refunded":
        return "bg-street-purple/20 text-street-purple border-street-purple/40";
      case "Refund Pending Approval":
        return "bg-street-amber/20 text-street-amber border-street-amber/40";
      case "Exchanged":
        return "bg-street-cyan/20 text-street-cyan border-street-cyan/40";
      default:
        return "bg-aether-800 text-aether-300 border-aether-700";
    }
  };

  const getStepIndex = (status: string) => {
    if (status === "Delivered") return 3;
    if (status === "In Transit") return 2;
    if (status === "Packed") return 1;
    if (status === "Processing") return 0;
    return -1;
  };

  const filteredOrders = orders.filter((o) => {
    if (filter === "Active") return ["Processing", "Packed", "In Transit"].includes(o.status);
    if (filter === "Delivered") return o.status === "Delivered";
    if (filter === "Refunds") return ["Cancelled", "Refunded", "Refund Pending Approval", "Exchanged"].includes(o.status);
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black font-mono tracking-tight text-white uppercase">
            My Streetwear Shipments
          </h1>
          <p className="text-xs font-mono text-aether-400 mt-1">
            Real-time delivery progress, BlueDart / Delhivery tracking, and 1-click returns.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-aether-900 border border-aether-800 text-xs font-mono">
          {["All", "Active", "Delivered", "Refunds"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                filter === f
                  ? "bg-white text-black font-bold shadow"
                  : "text-aether-400 hover:text-white"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* New Order Banner Alert */}
      {newOrderParam && (
        <div className="p-4 rounded-xl bg-street-emerald/10 border border-street-emerald/30 text-white font-mono text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-street-emerald shrink-0" />
            <span>
              Order <strong>{newOrderParam}</strong> created successfully! Live tracking is active below.
            </span>
          </div>
          <span className="text-[10px] text-street-emerald uppercase font-bold tracking-widest">
            Database Synced
          </span>
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 rounded-xl bg-street-cyan/10 border border-street-cyan/30 text-street-cyan font-mono text-xs flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-xs hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Orders List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 rounded-2xl bg-aether-900/40 border border-aether-800/60 animate-pulse" />
          ))}
        </div>
      ) : filteredOrders.length === 0 ? (
        <div className="py-20 text-center font-mono text-aether-500 space-y-3">
          <p>No orders found for the "{filter}" filter.</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white text-black text-xs font-bold hover:bg-aether-200 transition-colors shadow"
          >
            Start Shopping <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          {filteredOrders.map((order) => {
            const stepIndex = getStepIndex(order.status);
            const isCancellable = ["Processing", "Packed"].includes(order.status);
            const isDelivered = order.status === "Delivered";

            return (
              <div
                key={order.id}
                className="rounded-2xl bg-aether-900/60 border border-aether-800 p-6 space-y-6 shadow-xl transition-all hover:border-aether-700"
              >
                {/* Header Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-aether-850 pb-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="text-base font-black font-mono tracking-tight text-white">
                      {order.order_number}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full border text-xs font-mono font-bold uppercase tracking-wider ${getStatusBadge(order.status)}`}>
                      {order.status}
                    </span>
                    {order.carrier && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-aether-850 text-aether-300 border border-aether-700 flex items-center gap-1">
                        <Truck className="w-3 h-3 text-street-cyan" /> {order.carrier}: {order.tracking_number}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs font-mono text-aether-400">
                    <span>
                      Placed:{" "}
                      {new Date(order.created_at).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                    <span className="font-bold text-white text-sm">{formatINR(order.total_amount_inr)}</span>
                  </div>
                </div>

                {/* Visual Delivery Stepper (Only for active & delivered orders) */}
                {stepIndex >= 0 && (
                  <div className="py-2">
                    <div className="grid grid-cols-4 gap-2 relative">
                      {STATUS_STEPS.map((step, idx) => {
                        const isCompleted = idx <= stepIndex;
                        const isCurrent = idx === stepIndex;

                        return (
                          <div key={step} className="flex flex-col items-center text-center space-y-2">
                            <div
                              className={`w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs font-bold transition-all ${
                                isCompleted
                                  ? "bg-white text-black shadow-md ring-2 ring-white/20"
                                  : "bg-aether-950 text-aether-600 border border-aether-800"
                              }`}
                            >
                              {isCompleted ? <CheckCircle2 className="w-4 h-4 text-black" /> : idx + 1}
                            </div>
                            <span
                              className={`text-[11px] font-mono tracking-tight ${
                                isCurrent
                                  ? "text-white font-bold"
                                  : isCompleted
                                  ? "text-aether-300"
                                  : "text-aether-600"
                              }`}
                            >
                              {step}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Items Row */}
                <div className="space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-aether-500 block">
                    Garments Ordered
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {order.items.map((item) => (
                      <div
                        key={item.id}
                        className="p-3 rounded-xl bg-aether-950 border border-aether-850 flex items-center justify-between text-xs font-mono"
                      >
                        <div className="truncate mr-2">
                          <p className="text-white font-semibold truncate">{item.product_name}</p>
                          <p className="text-aether-500 text-[11px]">
                            SKU: {item.sku} • Size: <span className="text-aether-300 font-bold">{item.size}</span> • Qty: {item.quantity}
                          </p>
                        </div>
                        <span className="font-bold text-white shrink-0">
                          {formatINR(item.unit_price_inr * item.quantity)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Shipping Address & Payment Footer */}
                <div className="pt-2 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-mono text-aether-400">
                  <div className="max-w-md">
                    <span className="text-aether-500 uppercase text-[10px] block">Shipping Destination:</span>
                    <p className="text-aether-300 truncate">{order.shipping_address}</p>
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
                    {/* Cancellation Button */}
                    {isCancellable && (
                      <button
                        onClick={() => handleCancel(order.order_number)}
                        disabled={cancellingOrder === order.order_number}
                        className="px-3 py-1.5 rounded-lg bg-street-red/10 border border-street-red/30 hover:bg-street-red/20 text-street-red text-xs font-mono font-semibold transition-colors"
                      >
                        {cancellingOrder === order.order_number ? "Cancelling..." : "Cancel Order"}
                      </button>
                    )}

                    {/* AI Return / Exchange Prompt Button */}
                    {isDelivered && (
                      <div className="px-3 py-1.5 rounded-lg bg-street-cyan/10 border border-street-cyan/30 text-street-cyan text-xs font-mono flex items-center gap-1.5 font-semibold">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Eligible for Return / Exchange via AI Chat</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function MyOrdersPage() {
  return (
    <Suspense
      fallback={
        <div className="py-20 text-center font-mono text-aether-500">
          Loading shipments & orders...
        </div>
      }
    >
      <OrdersContent />
    </Suspense>
  );
}
