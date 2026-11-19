"use client";

import { useEffect, useState } from "react";
import { Product } from "@/types";
import { api } from "@/lib/api";
import { useCartStore } from "@/store/useCartStore";
import { formatINR } from "@/lib/utils";
import { Sparkles, ShoppingBag, Check, ShieldCheck, Truck, ArrowUpDown } from "lucide-react";
import Link from "next/link";

const CATEGORIES = ["All", "Hoodies", "Tees", "Bottoms", "Outerwear", "Accessories"];
const SIZES = ["All", "S", "M", "L", "XL"];

export default function StorefrontPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedSizeFilter, setSelectedSizeFilter] = useState("All");
  const [selectedSizes, setSelectedSizes] = useState<Record<number, string>>({});
  const [addedAnimation, setAddedAnimation] = useState<Record<number, boolean>>({});
  const [imageErrors, setImageErrors] = useState<Record<number, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);

  const { addItem } = useCartStore();

  useEffect(() => {
    async function loadProducts() {
      setIsLoading(true);
      try {
        const data = await api.getProducts({
          category: selectedCategory === "All" ? undefined : selectedCategory,
          size: selectedSizeFilter === "All" ? undefined : selectedSizeFilter,
        });
        setProducts(data);

        // Pre-select first available size for each product
        const initialSizes: Record<number, string> = {};
        data.forEach((p: Product) => {
          const firstInStock = Object.entries(p.sizes).find(([_, stock]) => stock > 0);
          initialSizes[p.id] = firstInStock ? firstInStock[0] : "M";
        });
        setSelectedSizes(initialSizes);
      } catch (err) {
        console.error("Failed to load products", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadProducts();
  }, [selectedCategory, selectedSizeFilter]);

  const handleAddToCart = (product: Product) => {
    const size = selectedSizes[product.id] || "M";
    addItem(product, size, 1);

    setAddedAnimation((prev) => ({ ...prev, [product.id]: true }));
    setTimeout(() => {
      setAddedAnimation((prev) => ({ ...prev, [product.id]: false }));
    }, 1200);
  };

  return (
    <div className="space-y-10">
      {/* Hero Streetwear Header Banner */}
      <section className="relative rounded-2xl overflow-hidden border border-aether-800 bg-gradient-to-b from-aether-900 to-aether-950 p-8 sm:p-12 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-aether-300 mb-4 uppercase tracking-widest">
          <span className="w-2 h-2 rounded-full bg-street-red animate-pulse" />
          AETHER INDIA // HEAVYWEIGHT ARCHIVE 2024
        </div>
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tighter text-white uppercase max-w-3xl mx-auto leading-none">
          LUXURY STREETWEAR. <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-aether-100 via-aether-400 to-aether-600">
            AUTONOMOUS AI COMMERCE.
          </span>
        </h1>
        <p className="mt-4 text-xs sm:text-sm font-mono text-aether-400 max-w-xl mx-auto leading-relaxed">
          Crafted in heavy Japanese cotton (240GSM – 480GSM) and 3-Layer Gore-Tex.
          Powered by a 4-Agent LangGraph supervisor with instant UPI order creation, automated refunds, and BlueDart / Delhivery dispatch.
        </p>

        {/* Feature Pills */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-[11px] font-mono text-aether-300">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-aether-850 border border-aether-800">
            <Truck className="w-3.5 h-3.5 text-street-emerald" /> Free Shipping ≥ ₹1,999
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-aether-850 border border-aether-800">
            <ShieldCheck className="w-3.5 h-3.5 text-street-cyan" /> 14-Day Free Returns (≤ ₹5k Auto)
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-aether-850 border border-aether-800">
            <Sparkles className="w-3.5 h-3.5 text-street-amber" /> 4-Agent Live Chat Assistant
          </div>
        </div>
      </section>

      {/* Filter and Category Controls */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-aether-850 pb-4">
        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0 no-scrollbar">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-mono tracking-wider transition-all uppercase whitespace-nowrap ${
                selectedCategory === cat
                  ? "bg-white text-black font-bold shadow-lg"
                  : "bg-aether-900 border border-aether-800 text-aether-400 hover:text-white hover:border-aether-700"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Size Filter Pills */}
        <div className="flex items-center gap-2 self-end md:self-auto text-xs font-mono">
          <span className="text-aether-500 uppercase tracking-wider">Size:</span>
          {SIZES.map((sz) => (
            <button
              key={sz}
              onClick={() => setSelectedSizeFilter(sz)}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                selectedSizeFilter === sz
                  ? "bg-aether-800 text-white font-bold border border-aether-600"
                  : "text-aether-400 hover:text-white"
              }`}
            >
              {sz}
            </button>
          ))}
        </div>
      </div>

      {/* Product Catalog Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-96 rounded-2xl bg-aether-900/40 border border-aether-800/60 animate-pulse" />
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="py-20 text-center font-mono text-aether-500">
          No garments found for the selected filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {products.map((product) => {
            const selectedSize = selectedSizes[product.id] || "M";
            const currentStock = product.sizes[selectedSize] ?? 0;
            const isOutOfStock = currentStock === 0;

            return (
              <div
                key={product.id}
                className="group flex flex-col rounded-2xl bg-aether-900/60 border border-aether-800 hover:border-aether-600 transition-all duration-300 overflow-hidden shadow-lg hover:shadow-2xl hover:-translate-y-1"
              >
                {/* Product Image / Visual Canvas */}
                <div className="relative h-64 bg-gradient-to-br from-aether-850 to-aether-950 p-4 flex flex-col justify-between overflow-hidden">
                  {/* Real Product Image with smooth hover zoom */}
                  {product.image_url && !imageErrors[product.id] ? (
                    <>
                      <img
                        src={product.image_url}
                        alt={product.name}
                        onError={() => setImageErrors((prev) => ({ ...prev, [product.id]: true }))}
                        className="absolute inset-0 w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500"
                      />
                      {/* Gradient overlay for text contrast */}
                      <div className="absolute inset-0 bg-gradient-to-t from-aether-950 via-transparent to-black/60 pointer-events-none" />
                    </>
                  ) : (
                    <>
                      {/* Subtle Grid Accent */}
                      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]" />

                      {/* Streetwear Typography Centerpiece (Fallback) */}
                      <div className="relative z-10 text-center my-auto">
                        <span className="font-mono text-3xl font-black tracking-tighter text-white/20 group-hover:text-white/40 transition-colors uppercase">
                          {product.sku.split("-")[1] || "AETH"}
                        </span>
                        <p className="text-[11px] font-mono text-aether-400 mt-1 uppercase tracking-widest">
                          {product.fit_type} Silhouette
                        </p>
                      </div>
                    </>
                  )}

                  {/* Top Badges */}
                  <div className="relative z-10 flex items-center justify-between gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono tracking-widest bg-black/70 backdrop-blur-md text-aether-300 border border-white/10 uppercase">
                      {product.category}
                    </span>
                    {product.fabric_gsm && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-street-red/90 text-white border border-street-red/30 font-semibold shadow-md">
                        {product.fabric_gsm} GSM
                      </span>
                    )}
                  </div>

                  {/* Bottom Stock Indicator */}
                  <div className="relative z-10 flex items-center justify-between text-[11px] font-mono bg-black/50 backdrop-blur-sm px-2 py-1 rounded-lg border border-white/5">
                    <span className="text-aether-300 text-[10px]">{product.sku}</span>
                    <span className={currentStock > 3 ? "text-street-emerald font-semibold" : currentStock > 0 ? "text-street-amber font-semibold" : "text-street-red font-semibold"}>
                      {currentStock > 0 ? `${currentStock} in stock` : "Sold Out"}
                    </span>
                  </div>
                </div>

                {/* Details Section */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight line-clamp-1 group-hover:text-street-amber transition-colors">
                      {product.name}
                    </h3>
                    <p className="text-xs text-aether-400 mt-1 line-clamp-2 leading-relaxed">
                      {product.description}
                    </p>
                  </div>

                  {/* Size Selector */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] font-mono text-aether-400">
                      <span>SELECT SIZE:</span>
                      <span className="text-white font-semibold">{selectedSize}</span>
                    </div>
                    <div className="grid grid-cols-4 gap-1">
                      {["S", "M", "L", "XL"].map((sz) => {
                        const stock = product.sizes[sz] || 0;
                        const disabled = stock === 0;
                        const isSelected = selectedSize === sz;

                        return (
                          <button
                            key={sz}
                            disabled={disabled}
                            onClick={() => setSelectedSizes((prev) => ({ ...prev, [product.id]: sz }))}
                            className={`py-1 rounded text-xs font-mono font-semibold transition-all ${
                              isSelected
                                ? "bg-white text-black font-bold shadow-md"
                                : disabled
                                ? "bg-aether-950 text-aether-700 cursor-not-allowed border border-aether-900"
                                : "bg-aether-850 hover:bg-aether-800 text-aether-300 border border-aether-800"
                            }`}
                          >
                            {sz}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Price & Add to Cart Button */}
                  <div className="pt-2 border-t border-aether-850 flex items-center justify-between gap-3">
                    <div>
                      <span className="text-[10px] font-mono text-aether-500 block">PRICE (INR)</span>
                      <span className="text-base font-black text-white font-mono tracking-tight">
                        {formatINR(product.price_inr)}
                      </span>
                    </div>

                    <button
                      onClick={() => handleAddToCart(product)}
                      disabled={isOutOfStock}
                      className={`flex-1 py-2 px-3 rounded-xl font-mono text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-lg ${
                        addedAnimation[product.id]
                          ? "bg-street-emerald text-white"
                          : isOutOfStock
                          ? "bg-aether-850 text-aether-600 cursor-not-allowed"
                          : "bg-white hover:bg-aether-200 text-black hover:scale-[1.02]"
                      }`}
                    >
                      {addedAnimation[product.id] ? (
                        <>
                          <Check className="w-3.5 h-3.5" /> Added!
                        </>
                      ) : isOutOfStock ? (
                        "Sold Out"
                      ) : (
                        <>
                          <ShoppingBag className="w-3.5 h-3.5" /> Add to Cart
                        </>
                      )}
                    </button>
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
