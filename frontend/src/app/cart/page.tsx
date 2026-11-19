"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";
import { api } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  Trash2,
  Plus,
  Minus,
  Truck,
  CreditCard,
  QrCode,
  Banknote,
  MapPin,
  CheckCircle2,
  ShoppingBag,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";

const PAYMENT_METHODS = [
  { id: "UPI", label: "UPI (Google Pay, PhonePe, Paytm)", icon: QrCode, badge: "Instant Verification" },
  { id: "Card", label: "Credit / Debit Card", icon: CreditCard, badge: "Visa / Mastercard / RuPay" },
  { id: "COD", label: "Cash on Delivery", icon: Banknote, badge: "Pay at Doorstep" },
];

export default function CartAndCheckoutPage() {
  const router = useRouter();
  const { items, updateQuantity, removeItem, clearCart, getSubtotal, getShippingFee, getTotal } =
    useCartStore();
  const { user, isAuthenticated, loginAsDemoCustomer } = useAuthStore();

  const [address, setAddress] = useState(
    user?.default_address || "Flat 402, Pinnacle Residency, Vijay Nagar, Indore, MP - 452010"
  );
  const [paymentMethod, setPaymentMethod] = useState("UPI");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const subtotal = getSubtotal();
  const shipping = getShippingFee();
  const total = getTotal();

  const handleCheckout = async () => {
    setError(null);

    if (items.length === 0) {
      setError("Your cart is empty.");
      return;
    }

    if (!address.trim()) {
      setError("Please provide a valid Indian shipping address.");
      return;
    }

    setIsSubmitting(true);
    try {
      // Auto-authenticate as demo customer if guest clicks place order
      if (!isAuthenticated) {
        await loginAsDemoCustomer();
      }

      const orderPayload = {
        items: items.map((it) => ({
          product_id: it.product.id,
          size: it.size,
          quantity: it.quantity,
        })),
        shipping_address: address,
        payment_method: paymentMethod,
      };

      const newOrder = await api.createOrder(orderPayload);
      clearCart();
      router.push(`/orders?new_order=${newOrder.order_number}`);
    } catch (err: any) {
      setError(err.message || "Failed to place order. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (items.length === 0) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-aether-900 border border-aether-800 flex items-center justify-center mx-auto text-aether-500">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold font-mono uppercase text-white">Your Cart is Empty</h2>
        <p className="text-xs font-mono text-aether-400 max-w-sm mx-auto">
          Explore our heavy Japanese cotton hoodies, ripstop cargo pants, and Gore-Tex shells.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-black font-mono text-xs font-bold hover:bg-aether-200 transition-colors shadow-lg"
        >
          Browse Streetwear Archive <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-black font-mono tracking-tight text-white uppercase">
          Cart &amp; Order Checkout
        </h1>
        <p className="text-xs font-mono text-aether-400 mt-1">
          Review your garments, verify shipping address, and choose payment.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-street-red/10 border border-street-red/30 text-street-red text-xs font-mono">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Items List */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-4 sm:p-6 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-4">
            <h2 className="text-xs font-mono font-bold tracking-widest text-aether-400 uppercase">
              Bag Items ({items.length})
            </h2>

            <div className="divide-y divide-aether-850">
              {items.map((it) => (
                <div key={`${it.product.id}-${it.size}`} className="py-4 first:pt-0 last:pb-0 flex gap-4">
                  {/* Product Thumbnail */}
                  <div className="w-20 h-20 rounded-xl bg-aether-950 border border-aether-800 shrink-0 font-mono text-xs font-bold text-aether-600 overflow-hidden relative flex items-center justify-center">
                    {it.product.image_url ? (
                      <img
                        src={it.product.image_url}
                        alt={it.product.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    ) : null}
                    <span className="absolute inset-0 flex items-center justify-center -z-0">
                      {it.product.sku.split("-")[1] || "AETH"}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0 flex flex-col justify-between">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-bold text-white tracking-tight truncate">
                          {it.product.name}
                        </h3>
                        <p className="text-xs font-mono text-aether-400 mt-0.5">
                          Size: <span className="text-white font-semibold">{it.size}</span> • {it.product.fit_type} Fit
                        </p>
                      </div>
                      <span className="text-sm font-black text-white font-mono shrink-0">
                        {formatINR(it.product.price_inr * it.quantity)}
                      </span>
                    </div>

                    {/* Quantity Selector & Delete */}
                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center border border-aether-800 rounded-lg bg-aether-950">
                        <button
                          onClick={() => updateQuantity(it.product.id, it.size, it.quantity - 1)}
                          className="p-1.5 hover:text-white text-aether-400 transition-colors"
                        >
                          <Minus className="w-3.5 h-3.5" />
                        </button>
                        <span className="px-3 text-xs font-mono font-bold text-white">
                          {it.quantity}
                        </span>
                        <button
                          onClick={() => updateQuantity(it.product.id, it.size, it.quantity + 1)}
                          className="p-1.5 hover:text-white text-aether-400 transition-colors"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <button
                        onClick={() => removeItem(it.product.id, it.size)}
                        className="text-aether-500 hover:text-street-red transition-colors text-xs flex items-center gap-1 font-mono"
                      >
                        <Trash2 className="w-3.5 h-3.5" /> Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Checkout Controls */}
        <div className="lg:col-span-5 space-y-6">
          {/* Shipping Address Box */}
          <div className="p-4 sm:p-6 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold tracking-widest text-aether-400 uppercase flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-street-red" /> Delivery Destination (India)
              </span>
              <span className="text-[10px] font-mono text-street-emerald">BlueDart / Delhivery SLA</span>
            </div>

            <textarea
              rows={3}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Full Street Address, Landmark, City, State, PIN code"
              className="w-full bg-aether-950 border border-aether-800 focus:border-white rounded-xl p-3 text-xs text-white placeholder-aether-600 focus:outline-none transition-colors font-mono leading-relaxed"
            />
            <p className="text-[10px] font-mono text-aether-500">
              Metro cities: BlueDart Express (2-3 days). Tier-2 &amp; others: Delhivery Standard (4-5 days).
            </p>
          </div>

          {/* Payment Method Selector */}
          <div className="p-4 sm:p-6 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-3">
            <span className="text-xs font-mono font-bold tracking-widest text-aether-400 uppercase block">
              Payment Method (₹ INR)
            </span>

            <div className="space-y-2">
              {PAYMENT_METHODS.map((pm) => {
                const Icon = pm.icon;
                const isSelected = paymentMethod === pm.id;

                return (
                  <label
                    key={pm.id}
                    onClick={() => setPaymentMethod(pm.id)}
                    className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                      isSelected
                        ? "bg-white/10 border-white text-white font-bold"
                        : "bg-aether-950 border-aether-800 text-aether-400 hover:border-aether-700"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${isSelected ? "bg-white text-black" : "bg-aether-900 text-aether-400"}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-xs font-mono font-semibold">{pm.label}</p>
                        <p className="text-[10px] font-mono text-aether-500">{pm.badge}</p>
                      </div>
                    </div>
                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${isSelected ? "border-white bg-white" : "border-aether-700"}`}>
                      {isSelected && <div className="w-2 h-2 rounded-full bg-black" />}
                    </div>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Price Breakdown & Place Order CTA */}
          <div className="p-4 sm:p-6 rounded-2xl bg-aether-900/60 border border-aether-800 space-y-4">
            <h2 className="text-xs font-mono font-bold tracking-widest text-aether-400 uppercase">
              Order Breakdown
            </h2>

            <div className="space-y-2 font-mono text-xs">
              <div className="flex justify-between text-aether-400">
                <span>Subtotal</span>
                <span className="text-white font-semibold">{formatINR(subtotal)}</span>
              </div>
              <div className="flex justify-between text-aether-400">
                <span className="flex items-center gap-1">
                  <Truck className="w-3.5 h-3.5" /> Shipping
                </span>
                <span className={shipping === 0 ? "text-street-emerald font-semibold" : "text-white"}>
                  {shipping === 0 ? "FREE" : formatINR(shipping)}
                </span>
              </div>
              {subtotal < 1999 && (
                <p className="text-[10px] text-street-amber">
                  Add {formatINR(1999 - subtotal)} more for free delivery.
                </p>
              )}
              <div className="pt-3 border-t border-aether-800 flex justify-between items-baseline text-sm">
                <span className="font-bold text-white uppercase tracking-wider">Total</span>
                <span className="text-xl font-black text-white">{formatINR(total)}</span>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              disabled={isSubmitting}
              className="w-full py-4 rounded-xl bg-white hover:bg-aether-200 text-black font-mono text-xs font-black uppercase tracking-wider transition-all shadow-xl disabled:opacity-50 flex items-center justify-center gap-2 hover:scale-[1.01]"
            >
              {isSubmitting ? (
                "Processing Order..."
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 text-black" />
                  Place Order • {formatINR(total)}
                </>
              )}
            </button>

            <p className="text-[10px] font-mono text-center text-aether-500">
              Orders update live in SQLite • Decrements inventory • Emits in-app alert
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
