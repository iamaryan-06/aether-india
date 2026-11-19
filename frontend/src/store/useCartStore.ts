import { create } from "zustand";
import { CartItem, Product } from "@/types";

interface CartState {
  items: CartItem[];
  addItem: (product: Product, size: string, quantity?: number) => void;
  removeItem: (productId: number, size: string) => void;
  updateQuantity: (productId: number, size: string, quantity: number) => void;
  clearCart: () => void;
  getSubtotal: () => number;
  getShippingFee: () => number;
  getTotal: () => number;
  getItemCount: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  items: [],

  addItem: (product: Product, size: string, quantity = 1) => {
    set((state) => {
      const existingIndex = state.items.findIndex(
        (it) => it.product.id === product.id && it.size.toUpperCase() === size.toUpperCase()
      );
      if (existingIndex > -1) {
        const updated = [...state.items];
        updated[existingIndex].quantity += quantity;
        return { items: updated };
      }
      return { items: [...state.items, { product, size: size.toUpperCase(), quantity }] };
    });
  },

  removeItem: (productId: number, size: string) => {
    set((state) => ({
      items: state.items.filter(
        (it) => !(it.product.id === productId && it.size.toUpperCase() === size.toUpperCase())
      ),
    }));
  },

  updateQuantity: (productId: number, size: string, quantity: number) => {
    if (quantity <= 0) {
      get().removeItem(productId, size);
      return;
    }
    set((state) => ({
      items: state.items.map((it) =>
        it.product.id === productId && it.size.toUpperCase() === size.toUpperCase()
          ? { ...it, quantity }
          : it
      ),
    }));
  },

  clearCart: () => set({ items: [] }),

  getSubtotal: () => {
    return get().items.reduce((acc, item) => acc + item.product.price_inr * item.quantity, 0);
  },

  getShippingFee: () => {
    const subtotal = get().getSubtotal();
    if (subtotal === 0) return 0;
    // Free shipping on orders >= ₹1,999
    return subtotal >= 1999 ? 0 : 99;
  },

  getTotal: () => {
    return get().getSubtotal() + get().getShippingFee();
  },

  getItemCount: () => {
    return get().items.reduce((acc, item) => acc + item.quantity, 0);
  },
}));
