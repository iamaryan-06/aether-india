"use client";

import { useEffect, useState, useRef } from "react";
import { Bell, CheckCheck, Package, RotateCcw, AlertTriangle, Info } from "lucide-react";
import { useNotificationStore } from "@/store/useNotificationStore";
import { useAuthStore } from "@/store/useAuthStore";
import Link from "next/link";

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { notifications, unreadCount, fetchNotifications, markAsRead, markAllAsRead } =
    useNotificationStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 15000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, fetchNotifications]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!isAuthenticated) return null;

  const getIcon = (type: string) => {
    switch (type) {
      case "ORDER_CONFIRMED":
      case "ORDER_SHIPPED":
        return <Package className="w-4 h-4 text-street-emerald" />;
      case "REFUND_PROCESSED":
      case "EXCHANGE_APPROVED":
        return <RotateCcw className="w-4 h-4 text-street-cyan" />;
      case "ESCALATION_LOGGED":
        return <AlertTriangle className="w-4 h-4 text-street-amber" />;
      default:
        return <Info className="w-4 h-4 text-aether-400" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2.5 rounded-full bg-aether-900 border border-aether-800 hover:border-aether-600 transition-colors text-aether-200 hover:text-white"
        aria-label="Notifications"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-street-red text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-84 sm:w-96 bg-aether-900/95 backdrop-blur-xl border border-aether-800 rounded-xl shadow-2xl z-50 overflow-hidden">
          <div className="p-4 border-b border-aether-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-widest font-mono text-aether-400">Activity Log</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 text-[10px] bg-street-red/20 text-street-red rounded-full font-mono font-semibold">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllAsRead()}
                className="text-xs text-aether-400 hover:text-white flex items-center gap-1 transition-colors"
              >
                <CheckCheck className="w-3.5 h-3.5" /> Mark read
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto divide-y divide-aether-850">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-aether-500 text-sm font-mono">
                No recent activity logged.
              </div>
            ) : (
              notifications.slice(0, 8).map((notif) => (
                <div
                  key={notif.id}
                  onClick={() => !notif.is_read && markAsRead(notif.id)}
                  className={`p-4 transition-colors cursor-pointer flex gap-3 ${
                    notif.is_read ? "bg-transparent opacity-75 hover:opacity-100" : "bg-aether-850/60 hover:bg-aether-800/60"
                  }`}
                >
                  <div className="mt-0.5 p-1.5 rounded-lg bg-aether-950 border border-aether-800 shrink-0">
                    {getIcon(notif.notification_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-semibold text-white truncate">{notif.title}</p>
                      {!notif.is_read && <span className="w-1.5 h-1.5 bg-street-red rounded-full shrink-0" />}
                    </div>
                    <p className="text-xs text-aether-400 mt-1 line-clamp-2 leading-relaxed">
                      {notif.message}
                    </p>
                    <span className="text-[10px] font-mono text-aether-500 mt-1.5 block">
                      {new Date(notif.created_at).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-3 border-t border-aether-800 text-center bg-aether-950/60">
            <Link
              href="/orders"
              onClick={() => setIsOpen(false)}
              className="text-xs font-mono text-aether-400 hover:text-white transition-colors"
            >
              View Orders & Shipments →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
