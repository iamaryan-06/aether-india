"use client";

import { useEffect, useState } from "react";
import { Order } from "@/types";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { formatINR } from "@/lib/utils";
import {
  Package,
  Truck,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Search,
  Filter,
} from "lucide-react";

const ORDER_STATUSES = [
  "All",
  "Processing",
  "Packed",
  "In Transit",
  "Delivered",
  "Cancelled",
  "Refund Pending Approval",
  "Refunded",
  "Exchanged",
];

export default function AdminOrdersManagerPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [statusFilter, setStatusFilter] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [updatingOrder, setUpdatingOrder] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const { user, loginAsDemoAdmin } = useAuthStore();

  const loadOrders = async () => {
    setIsLoading(true);
    try {
      if (!user || user.role !== "admin") {
        await loginAsDemoAdmin();
      }
      const data = await api.getAdminOrders(statusFilter === "All" ? undefined : statusFilter);
      setOrders(data);
    } catch (err) {
      console.error("Failed to load orders", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [user, statusFilter]);

  const handleStatusChange = async (orderNumber: string, newStatus: string) => {
    setUpdatingOrder(orderNumber);
    setFeedback(null);
    try {
      await api.updateOrderStatus(orderNumber, {
        status: newStatus,
        carrier: newStatus === "In Transit" ? "BlueDart" : undefined,
        tracking_number: newStatus === "In Transit" ? `BD${Math.floor(10000000000 + Math.random() * 90000000000)}` : undefined,
      });
      setFeedback(`Order ${orderNumber} updated to status '${newStatus}'`);
      await loadOrders();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    } finally {
      setUpdatingOrder(null);
    }
  };

  const filteredOrders = orders.filter((o) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      o.order_number.toLowerCase().includes(query) ||
      o.shipping_address.toLowerCase().includes(query) ||
      (o.tracking_number && o.tracking_number.toLowerCase().includes(query))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black font-mono tracking-tight text-white uppercase flex items-center gap-2">
            <Package className="w-6 h-6 text-street-cyan" />
            Operations Order Manager
          </h1>
          <p className="text-xs font-mono text-aether-400 mt-1">
            Track customer orders, advance shipping status, and update logistics tracking.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-3 text-aether-500" />
          <input
            type="text"
            placeholder="Search order number or city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-aether-900 border border-aether-800 focus:border-white rounded-xl pl-9 pr-4 py-2 text-xs font-mono text-white placeholder-aether-500 focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar pb-1 text-xs font-mono">
        {ORDER_STATUSES.map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
              statusFilter === st
                ? "bg-white text-black font-bold shadow"
                : "bg-aether-900 border border-aether-800 text-aether-400 hover:text-white"
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl bg-street-emerald/10 border border-street-emerald/30 text-street-emerald font-mono text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="text-xs hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Orders Table */}
      <div className="rounded-2xl bg-aether-900/60 border border-aether-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-aether-950 border-b border-aether-850 text-[10px] uppercase text-aether-500 tracking-wider">
              <tr>
                <th className="p-4">Order / Placed</th>
                <th className="p-4">Garments Ordered</th>
                <th className="p-4">Delivery City &amp; Carrier</th>
                <th className="p-4">Amount &amp; Payment</th>
                <th className="p-4">Status &amp; Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-aether-850">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-aether-500">
                    Loading orders...
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-aether-500">
                    No orders match the selected criteria.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-aether-850/40 transition-colors">
                    {/* Order / Placed */}
                    <td className="p-4 space-y-1">
                      <span className="font-bold text-white text-sm block">{ord.order_number}</span>
                      <span className="text-[10px] text-aether-400">
                        {new Date(ord.created_at).toLocaleDateString("en-IN", {
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </td>

                    {/* Garments Ordered */}
                    <td className="p-4">
                      <div className="space-y-1 max-w-xs">
                        {ord.items.map((it) => (
                          <div key={it.id} className="truncate">
                            <span className="text-white font-semibold">{it.product_name}</span>{" "}
                            <span className="text-aether-400 text-[11px]">
                              ({it.size} x {it.quantity})
                            </span>
                          </div>
                        ))}
                      </div>
                    </td>

                    {/* Delivery City & Carrier */}
                    <td className="p-4 space-y-1">
                      <p className="text-aether-300 truncate max-w-xs">{ord.shipping_address}</p>
                      <div className="flex items-center gap-1.5 text-[10px]">
                        <Truck className="w-3 h-3 text-street-cyan shrink-0" />
                        <span className="text-street-cyan font-semibold">
                          {ord.carrier || "Unassigned"}:
                        </span>
                        <span className="text-aether-400">{ord.tracking_number || "Pending"}</span>
                      </div>
                    </td>

                    {/* Amount & Payment */}
                    <td className="p-4 space-y-1">
                      <span className="font-black text-white text-sm block">
                        {formatINR(ord.total_amount_inr)}
                      </span>
                      <div className="flex items-center gap-1.5 text-[10px]">
                        <span className="text-aether-400">{ord.payment_method}</span>
                        <span
                          className={`px-1.5 py-0.2 rounded font-bold uppercase ${
                            ord.payment_status === "Paid"
                              ? "bg-street-emerald/20 text-street-emerald"
                              : ord.payment_status === "Refunded"
                              ? "bg-street-purple/20 text-street-purple"
                              : "bg-street-amber/20 text-street-amber"
                          }`}
                        >
                          {ord.payment_status}
                        </span>
                      </div>
                    </td>

                    {/* Status & Actions Dropdown */}
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <select
                          value={ord.status}
                          disabled={updatingOrder === ord.order_number}
                          onChange={(e) => handleStatusChange(ord.order_number, e.target.value)}
                          className="bg-aether-950 border border-aether-800 text-white rounded-lg px-2.5 py-1.5 text-xs font-mono focus:border-white focus:outline-none transition-colors"
                        >
                          <option value="Processing">Processing</option>
                          <option value="Packed">Packed</option>
                          <option value="In Transit">In Transit</option>
                          <option value="Delivered">Delivered</option>
                          <option value="Cancelled">Cancelled</option>
                          <option value="Refund Pending Approval">Refund Pending Approval</option>
                          <option value="Refunded">Refunded</option>
                          <option value="Exchanged">Exchanged</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
