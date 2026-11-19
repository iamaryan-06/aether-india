"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ShoppingBag, Sparkles, User as UserIcon, Shield, LogOut } from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { useCartStore } from "@/store/useCartStore";
import NotificationBell from "./NotificationBell";

interface NavbarProps {
  onOpenChat?: () => void;
}

export default function Navbar({ onOpenChat }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();
  const itemCount = useCartStore((state) => state.getItemCount());

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-aether-800/80 bg-aether-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="font-mono text-lg font-black tracking-tighter text-white uppercase group-hover:text-street-amber transition-colors">
              AETHER<span className="text-aether-500 font-normal ml-1">INDIA</span>
            </span>
            <span className="hidden sm:inline-block px-1.5 py-0.5 text-[9px] font-mono tracking-widest bg-aether-800 text-aether-300 rounded border border-aether-700 uppercase">
              Streetwear // AI Ops
            </span>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-5 text-xs font-mono tracking-wider uppercase">
            <Link
              href="/"
              className={`transition-colors hover:text-white ${
                pathname === "/" ? "text-white font-semibold" : "text-aether-400"
              }`}
            >
              Archive / Shop
            </Link>
            <Link
              href="/orders"
              className={`transition-colors hover:text-white ${
                pathname === "/orders" ? "text-white font-semibold" : "text-aether-400"
              }`}
            >
              My Orders
            </Link>
            {user?.role === "admin" && (
              <Link
                href="/admin"
                className="px-2 py-0.5 rounded bg-street-red/10 border border-street-red/30 text-street-red hover:bg-street-red/20 transition-colors flex items-center gap-1 font-semibold"
              >
                <Shield className="w-3 h-3" /> Admin Ops
              </Link>
            )}
          </nav>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {/* AI Multi-Agent Trigger Pill */}
          <button
            onClick={onOpenChat}
            className="relative px-3.5 py-1.5 rounded-full bg-gradient-to-r from-street-red/20 via-street-purple/20 to-street-cyan/20 border border-white/10 hover:border-street-amber/50 text-xs font-mono text-white transition-all flex items-center gap-1.5 shadow-lg group hover:scale-105"
          >
            <Sparkles className="w-3.5 h-3.5 text-street-amber group-hover:rotate-12 transition-transform" />
            <span className="hidden sm:inline font-semibold">4-Agent AI</span>
            <span className="sm:hidden font-semibold">AI</span>
            <span className="w-1.5 h-1.5 rounded-full bg-street-emerald animate-ping" />
          </button>

          {/* Notification Bell */}
          <NotificationBell />

          {/* Cart Icon Button */}
          <Link
            href="/cart"
            className="relative p-2.5 rounded-full bg-aether-900 border border-aether-800 hover:border-aether-600 transition-colors text-aether-200 hover:text-white"
            aria-label="Cart"
          >
            <ShoppingBag className="w-4 h-4" />
            {itemCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-white text-black text-[10px] font-bold rounded-full flex items-center justify-center font-mono">
                {itemCount}
              </span>
            )}
          </Link>

          {/* Auth State */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2 pl-2 border-l border-aether-800">
              <div className="hidden lg:block text-right">
                <p className="text-xs font-semibold text-white leading-tight truncate max-w-[120px]">{user.name}</p>
                <span className="text-[10px] font-mono text-aether-400 capitalize">{user.role}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-2 rounded-full hover:bg-aether-800 text-aether-400 hover:text-street-red transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="px-3 py-1.5 rounded-lg bg-aether-900 border border-aether-800 hover:border-aether-600 text-xs font-mono text-white transition-colors flex items-center gap-1.5"
            >
              <UserIcon className="w-3.5 h-3.5 text-aether-400" />
              <span>Login</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
