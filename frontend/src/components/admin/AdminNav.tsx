"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import {
  LayoutDashboard,
  ShieldAlert,
  Package,
  Boxes,
  ScrollText,
  ShieldCheck,
  UserCheck,
  LogOut,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const ADMIN_LINKS = [
  { href: "/admin", label: "KPI Overview", icon: LayoutDashboard },
  { href: "/admin/approvals", label: "HITL Approvals", icon: ShieldAlert, badge: true },
  { href: "/admin/orders", label: "Order Manager", icon: Package },
  { href: "/admin/inventory", label: "Inventory Matrix", icon: Boxes },
  { href: "/admin/agent-logs", label: "Agent Audit Logs", icon: ScrollText },
];

export default function AdminNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout, loginAsDemoAdmin } = useAuthStore();
  const [pendingCount, setPendingCount] = useState<number>(1);

  useEffect(() => {
    async function loadPending() {
      try {
        const appr = await api.getAdminApprovals("PENDING_ADMIN");
        setPendingCount(appr.length);
      } catch {}
    }
    if (user?.role === "admin") {
      loadPending();
    }
  }, [user, pathname]);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="space-y-4 mb-6">
      {/* Role / Auth Check Banner */}
      {(!isAuthenticated || user?.role !== "admin") && (
        <div className="p-4 rounded-xl bg-street-amber/10 border border-street-amber/30 text-street-amber font-mono text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>
              You are currently not signed in as an AETHER Administrator. Click below for 1-click Ops access.
            </span>
          </div>
          <button
            onClick={() => loginAsDemoAdmin()}
            className="px-3.5 py-1.5 rounded-lg bg-street-amber text-black font-bold hover:bg-street-amber/90 transition-colors shrink-0 flex items-center gap-1.5"
          >
            <UserCheck className="w-3.5 h-3.5" /> Switch to Admin (admin@aether.in)
          </button>
        </div>
      )}

      {/* Admin Sub-Navigation Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-aether-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-street-red/20 text-street-red border border-street-red/30">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-mono font-black tracking-wider text-white uppercase">
              Operations Head Console
            </h1>
            <p className="text-[10px] font-mono text-aether-400">AETHER INDIA Autonomous Business Ops</p>
          </div>
        </div>

        {/* Right side: Tab Links + Logout */}
        <div className="flex items-center gap-2">
          {/* Tab Links */}
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar pb-1 sm:pb-0">
            {ADMIN_LINKS.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center gap-1.5 whitespace-nowrap ${
                    isActive
                      ? "bg-white text-black font-bold shadow-md"
                      : "text-aether-400 hover:text-white hover:bg-aether-900 border border-transparent hover:border-aether-800"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{link.label}</span>
                  {link.badge && pendingCount > 0 && (
                    <span
                      className={`ml-1 px-1.5 py-0.2 rounded-full text-[9px] font-bold ${
                        isActive ? "bg-street-red text-white" : "bg-street-red/20 text-street-red"
                      }`}
                    >
                      {pendingCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>

          {/* Logout Button — only shown when logged in as admin */}
          {isAuthenticated && user?.role === "admin" && (
            <button
              onClick={handleLogout}
              title="Logout from Admin"
              className="ml-1 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono text-aether-400 hover:text-street-red hover:bg-street-red/10 border border-transparent hover:border-street-red/30 transition-all whitespace-nowrap"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
