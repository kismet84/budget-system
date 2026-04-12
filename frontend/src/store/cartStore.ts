import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { CartItem } from '../types/quota'

interface CartStore {
  items: CartItem[]
  addItem: (item: CartItem) => void
  removeItem: (quota_id: string) => void
  updateQuantity: (quota_id: string, quantity: number) => void
  clearCart: () => void
  totalCost: () => number
  totalLabor: () => number
  totalMaterial: () => number
  totalMachinery: () => number
  totalManagement: () => number
  totalTax: () => number
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (item) => {
        const exists = get().items.find((i) => i.quota_id === item.quota_id)
        if (!exists) {
          set((state) => ({ items: [...state.items, item] }))
        }
      },
      removeItem: (quota_id) => {
        set((state) => ({ items: state.items.filter((i) => i.quota_id !== quota_id) }))
      },
      updateQuantity: (quota_id, quantity) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.quota_id === quota_id ? { ...i, quantity } : i
          ),
        }))
      },
      clearCart: () => set({ items: [] }),
      totalCost: () => get().items.reduce((sum, i) => sum + (i.total_cost ?? 0) * i.quantity, 0),
      totalLabor: () => get().items.reduce((sum, i) => sum + (i.labor_fee ?? 0) * i.quantity, 0),
      totalMaterial: () => get().items.reduce((sum, i) => sum + (i.material_fee ?? 0) * i.quantity, 0),
      totalMachinery: () => get().items.reduce((sum, i) => sum + (i.machinery_fee ?? 0) * i.quantity, 0),
      totalManagement: () => get().items.reduce((sum, i) => sum + (i.management_fee ?? 0) * i.quantity, 0),
      totalTax: () => get().items.reduce((sum, i) => sum + (i.tax ?? 0) * i.quantity, 0),
    }),
    { name: 'budget-cart' }
  )
)
