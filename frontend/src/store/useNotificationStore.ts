import { create } from "zustand";
import { NotificationItem } from "@/types";
import { api } from "@/lib/api";

interface NotificationState {
  notifications: NotificationItem[];
  unreadCount: number;
  isLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  fetchNotifications: async () => {
    try {
      const data: NotificationItem[] = await api.getNotifications();
      const unread = data.filter((n) => !n.is_read).length;
      set({ notifications: data, unreadCount: unread });
    } catch {
      // User might be unauthenticated, silence
    }
  },

  markAsRead: async (id: number) => {
    try {
      await api.markNotificationRead(id);
      set((state) => {
        const updated = state.notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n));
        const unread = updated.filter((n) => !n.is_read).length;
        return { notifications: updated, unreadCount: unread };
      });
    } catch (err) {
      console.error("Failed to mark notification read", err);
    }
  },

  markAllAsRead: async () => {
    try {
      await api.markAllNotificationsRead();
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
        unreadCount: 0,
      }));
    } catch (err) {
      console.error("Failed to mark all read", err);
    }
  },
}));
