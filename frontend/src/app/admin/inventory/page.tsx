"use client";

import { useEffect, useState } from "react";
import { Product } from "@/types";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { formatINR } from "@/lib/utils";
import { Boxes, Plus, Minus, Check, RefreshCw, AlertTriangle } from "lucide-react";

export default function AdminInventoryPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingStock, setEditingStock] = useState<Record<number, Record<string, number>>>({});
  const [savingId, setSavingId] = useState<number | null>(null);
  const [successFeedback, setSuccessFeedback] = useState<string | null>(null);

  const { user, loginAsDemoAdmin } = useAuthStore();

  const loadInventory = async () => {
    setIsLoading(true);
    try {
      if (!user || user.role !== "admin") {
        await loginAsDemoAdmin();
      }
      const data = await api.getAdminInventory();
      setProducts(data);

      const stockMap: Record<number, Record<string, number>> = {};
      data.forEach((p: Product) => {
        stockMap[p.id] = { ...p.sizes };
      });
      setEditingStock(stockMap);
    } catch (err) {
      console.error("Failed to load inventory", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInventory();
  }, [user]);

  const handleStockDelta = (productId: number, size: string, delta: number) => {
    setEditingStock((prev) => {
      const current = prev[productId] || {};
      const val = Math.max(0, (current[size] ?? 0) + delta);
      return {
        ...prev,
        [productId]: {
          ...current,
          [size]: val,
        },
      };
    });
  };

  const handleSaveStock = async (productId: number) => {
    const updatedSizes = editingStock[productId];
    if (!updatedSizes) return;

    setSavingId(productId);
    setSuccessFeedback(null);
    try {
      const updatedProduct = await api.updateProductStock(productId, updatedSizes);
      setProducts((prev) => prev.map((p) => (p.id === productId ? updatedProduct : p)));
      setSuccessFeedback(`Stock updated for ${updatedProduct.name}`);
    } catch (err: any) {
      alert(`Failed to save stock: ${err.message}`);
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black font-mono tracking-tight text-white uppercase flex items-center gap-2">
            <Boxes className="w-6 h-6 text-street-purple" />
            Inventory &amp; Size-Level Stock Matrix
          </h1>
          <p className="text-xs font-mono text-aether-400 mt-1">
            Real-time stock control across S, M, L, XL sizes in SQLite database.
          </p>
        </div>

        <button
          onClick={loadInventory}
          className="px-3.5 py-2 rounded-xl bg-aether-900 border border-aether-800 hover:border-aether-600 text-xs font-mono text-white transition-colors flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Stock
        </button>
      </div>

      {successFeedback && (
        <div className="p-3.5 rounded-xl bg-street-emerald/10 border border-street-emerald/30 text-street-emerald font-mono text-xs flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Check className="w-4 h-4" /> {successFeedback}
          </span>
          <button onClick={() => setSuccessFeedback(null)} className="text-xs hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Inventory Matrix Table */}
      <div className="rounded-2xl bg-aether-900/60 border border-aether-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-aether-950 border-b border-aether-850 text-[10px] uppercase text-aether-500 tracking-wider">
              <tr>
                <th className="p-4">SKU / Garment</th>
                <th className="p-4">Silhouette &amp; GSM</th>
                <th className="p-4 text-center">Size S</th>
                <th className="p-4 text-center">Size M</th>
                <th className="p-4 text-center">Size L</th>
                <th className="p-4 text-center">Size XL</th>
                <th className="p-4 text-center">Total Units</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-aether-850">
              {isLoading ? (
                <tr>
                  <td colSpan={8} className="p-12 text-center text-aether-500">
                    Loading inventory matrix...
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const sizes = editingStock[p.id] || p.sizes;
                  const total = Object.values(sizes).reduce((a, b) => a + b, 0);

                  return (
                    <tr key={p.id} className="hover:bg-aether-850/40 transition-colors">
                      {/* SKU / Garment */}
                      <td className="p-4 space-y-1">
                        <span className="font-bold text-white text-sm block">{p.name}</span>
                        <span className="text-[10px] text-aether-400">{p.sku} • {formatINR(p.price_inr)}</span>
                      </td>

                      {/* Silhouette & GSM */}
                      <td className="p-4 space-y-1">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-aether-850 border border-aether-700 text-aether-300 font-semibold uppercase">
                          {p.fit_type}
                        </span>
                        {p.fabric_gsm && (
                          <span className="text-[10px] text-street-amber block">
                            {p.fabric_gsm} GSM
                          </span>
                        )}
                      </td>

                      {/* Size Controls: S, M, L, XL */}
                      {["S", "M", "L", "XL"].map((sz) => {
                        const count = sizes[sz] ?? 0;
                        const isLow = count < 5 && count > 0;
                        const isOut = count === 0;

                        return (
                          <td key={sz} className="p-4 text-center">
                            <div className="inline-flex items-center gap-1 border border-aether-800 rounded-lg bg-aether-950 p-1">
                              <button
                                onClick={() => handleStockDelta(p.id, sz, -1)}
                                className="p-1 hover:text-white text-aether-500 transition-colors"
                              >
                                <Minus className="w-3 h-3" />
                              </button>
                              <span
                                className={`w-8 text-center text-xs font-bold ${
                                  isOut
                                    ? "text-street-red"
                                    : isLow
                                    ? "text-street-amber"
                                    : "text-white"
                                }`}
                              >
                                {count}
                              </span>
                              <button
                                onClick={() => handleStockDelta(p.id, sz, 1)}
                                className="p-1 hover:text-white text-aether-500 transition-colors"
                              >
                                <Plus className="w-3 h-3" />
                              </button>
                            </div>
                          </td>
                        );
                      })}

                      {/* Total Stock */}
                      <td className="p-4 text-center">
                        <span className="font-black text-white text-sm block">{total}</span>
                        {total < 15 && (
                          <span className="text-[9px] text-street-amber font-semibold uppercase">
                            Low Restock
                          </span>
                        )}
                      </td>

                      {/* Save Action */}
                      <td className="p-4 text-right">
                        <button
                          onClick={() => handleSaveStock(p.id)}
                          disabled={savingId === p.id}
                          className="px-3 py-1.5 rounded-lg bg-white hover:bg-aether-200 text-black text-xs font-bold transition-all disabled:opacity-50 shadow"
                        >
                          {savingId === p.id ? "Saving..." : "Save Stock"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
