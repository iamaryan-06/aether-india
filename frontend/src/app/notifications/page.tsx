"use client";

import { useEffect } from "react";
import { useNotificationStore } from "@/store/useNotificationStore";
import { useAuthStore } from "@/store/useAuthStore";
import { Package, RotateCcw, AlertTriangle, Info, CheckCheck } from "lucide-react";
import Link from "next/link";

export default function NotificationsPage() {
  const { notifications, fetchNotifications, markAsRead, markAllAsRead, unreadCount } =
    useNotificationStore();
  const { isAuthenticated, loginAsDemoCustomer } = useAuthStore();

  useEffect(() => {
    async function init() {
      if (!isAuthenticated) {
        await loginAsDemoCustomer();
      }
      fetchNotifications();
    }
    init();
  }, [isAuthenticated, fetchNotifications]);

  const getIcon = (type: string) => {
    switch (type) {
      case "ORDER_CONFIRMED":
      case "ORDER_SHIPPED":
        return <Package className="w-5 h-5 text-street-emerald" />;
      case "REFUND_PROCESSED":
      case "EXCHANGE_APPROVED":
        return <RotateCcw className="w-5 h-5 text-street-cyan" />;
      case "ESCALATION_LOGGED":
        return <AlertTriangle className="w-5 h-5 text-street-amber" />;
      default:
        return <Info className="w-5 h-5 text-aether-400" />;
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black font-mono tracking-tight text-white uppercase">
            Notifications &amp; Activity
          </h1>
          <p className="text-xs font-mono text-aether-400 mt-1">
            Real-time events emitted by the 4-Agent LangGraph System.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={() => markAllAsRead()}
            className="px-3 py-1.5 rounded-lg bg-aether-900 border border-aether-800 hover:border-aether-600 text-xs font-mono text-white transition-colors flex items-center gap-1.5"
          >
            <CheckCheck className="w-4 h-4 text-street-emerald" /> Mark all read
          </button>
        )}
      </div>

      <div className="rounded-2xl bg-aether-900/60 border border-aether-800 divide-y divide-aether-850 overflow-hidden shadow-xl">
        {notifications.length === 0 ? (
          <div className="p-12 text-center text-aether-500 font-mono text-xs">
            No notifications logged for your account yet.
          </div>
        ) : (
          notifications.map((notif) => (
            <div
              key={notif.id}
              onClick={() => !notif.is_read && markAsRead(notif.id)}
              className={`p-5 flex items-start gap-4 transition-colors cursor-pointer ${
                notif.is_read ? "bg-transparent opacity-75 hover:opacity-100" : "bg-aether-850/50 hover:bg-aether-800/50"
              }`}
            >
              <div className="p-2 rounded-xl bg-aether-950 border border-aether-800 shrink-0">
                {getIcon(notif.notification_type)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-bold text-white font-mono">{notif.title}</h3>
                  <span className="text-[10px] font-mono text-aether-500 shrink-0">
                    {new Date(notif.created_at).toLocaleDateString("en-IN", {
                      day: "2-digit",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                <p className="text-xs text-aether-300 mt-1 font-mono leading-relaxed">
                  {notif.message}
                </p>
              </div>

              {!notif.is_read && (
                <span className="w-2 h-2 rounded-full bg-street-red shrink-0 mt-2" />
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
