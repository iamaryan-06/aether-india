import { create } from "zustand";
import { User } from "@/types";
import { api } from "@/lib/api";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  loginAsDemoCustomer: () => Promise<User>;
  loginAsDemoAdmin: () => Promise<User>;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,

  loadFromStorage: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("aether_token");
    const userStr = localStorage.getItem("aether_user");
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ user, token, isAuthenticated: true });
      } catch {
        localStorage.removeItem("aether_token");
        localStorage.removeItem("aether_user");
      }
    }
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const data = await api.login(email, password);
      const { access_token, user } = data;
      localStorage.setItem("aether_token", access_token);
      localStorage.setItem("aether_user", JSON.stringify(user));
      set({ user, token: access_token, isAuthenticated: true, isLoading: false });
      return user;
    } catch (err) {
      set({ isLoading: false });
      throw err;
    }
  },

  loginAsDemoCustomer: async () => {
    return get().login("aarav@customer.com", "Demo@1234");
  },

  loginAsDemoAdmin: async () => {
    return get().login("admin@aether.in", "Demo@1234");
  },

  logout: () => {
    localStorage.removeItem("aether_token");
    localStorage.removeItem("aether_user");
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
