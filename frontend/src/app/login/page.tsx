"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Shield, User, ArrowRight, Sparkles, Lock, Mail } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const { login, loginAsDemoCustomer, loginAsDemoAdmin, isLoading } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const user = await login(email, password);
      if (user.role === "admin") {
        router.push("/admin");
      } else {
        router.push("/");
      }
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
    }
  };

  const handleDemoCustomer = async () => {
    setError(null);
    try {
      await loginAsDemoCustomer();
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Customer login failed");
    }
  };

  const handleDemoAdmin = async () => {
    setError(null);
    try {
      await loginAsDemoAdmin();
      router.push("/admin");
    } catch (err: any) {
      setError(err.message || "Admin login failed");
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4 sm:px-0">
      <div className="rounded-2xl bg-aether-900/80 border border-aether-800 p-8 shadow-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-white/5 border border-white/10 text-white mb-2">
            <Lock className="w-6 h-6 text-street-amber" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white uppercase font-mono">
            AETHER Portal Login
          </h1>
          <p className="text-xs font-mono text-aether-400">
            Sign in to access your orders, track shipments, or manage ops.
          </p>
        </div>

        {/* 1-Click Fast Demo Buttons */}
        <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2 text-[10px] font-mono text-aether-500 uppercase tracking-widest">
            <Sparkles className="w-3 h-3 text-street-amber" />
            <span>1-Click Project Demo Access</span>
          </div>

          {/* Customer Demo Button */}
          <button
            type="button"
            onClick={handleDemoCustomer}
            disabled={isLoading}
            className="w-full p-3.5 rounded-xl bg-aether-850 hover:bg-aether-800 border border-aether-700 hover:border-aether-500 text-left transition-all group flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-street-cyan/10 text-street-cyan border border-street-cyan/20">
                <User className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-white font-mono group-hover:text-street-cyan transition-colors">
                  Login as Customer (Aarav Sharma)
                </p>
                <p className="text-[10px] font-mono text-aether-400">aarav@customer.com • 4 Seeded Orders</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-aether-500 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
          </button>

          {/* Admin Demo Button */}
          <button
            type="button"
            onClick={handleDemoAdmin}
            disabled={isLoading}
            className="w-full p-3.5 rounded-xl bg-street-red/10 hover:bg-street-red/20 border border-street-red/30 hover:border-street-red/50 text-left transition-all group flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-street-red/20 text-street-red border border-street-red/40">
                <Shield className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-white font-mono group-hover:text-street-red transition-colors">
                  Login as Operations Head (Admin)
                </p>
                <p className="text-[10px] font-mono text-aether-400">admin@aether.in • HITL Approval Queue</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-aether-500 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
          </button>
        </div>

        {/* Divider */}
        <div className="relative py-2">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-aether-800" />
          </div>
          <div className="relative flex justify-center text-[10px] uppercase font-mono">
            <span className="bg-aether-900 px-3 text-aether-500">Or Manual Sign In</span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 rounded-xl bg-street-red/10 border border-street-red/30 text-street-red text-xs font-mono">
            {error}
          </div>
        )}

        {/* Standard Credentials Form */}
        <form onSubmit={handleCustomLogin} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-[11px] font-mono text-aether-400 uppercase tracking-wider block">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-3 text-aether-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="aarav@customer.com"
                required
                className="w-full bg-aether-950 border border-aether-800 focus:border-white rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-aether-600 focus:outline-none transition-colors font-mono"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[11px] font-mono text-aether-400 uppercase tracking-wider block">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-3 text-aether-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-aether-950 border border-aether-800 focus:border-white rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-aether-600 focus:outline-none transition-colors font-mono"
              />
            </div>
            <p className="text-[10px] font-mono text-aether-500 text-right">Demo Password: Demo@1234</p>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 rounded-xl bg-white hover:bg-aether-200 text-black font-mono text-xs font-bold transition-all disabled:opacity-50 shadow-lg"
          >
            {isLoading ? "Authenticating..." : "Sign In →"}
          </button>
        </form>

        <div className="text-center text-[11px] font-mono text-aether-500">
          <Link href="/" className="hover:text-white transition-colors">
            ← Return to Streetwear Storefront
          </Link>
        </div>
      </div>
    </div>
  );
}
