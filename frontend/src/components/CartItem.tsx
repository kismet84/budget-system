import { Trash2 } from 'lucide-react'
import type { CartItem } from '../types/quota'

interface Props {
  item: CartItem
  onRemove: (quota_id: string) => void
  onQuantityChange: (quota_id: string, qty: number) => void
}

export default function CartItemRow({ item, onRemove, onQuantityChange }: Props) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-blue-400 text-sm">{item.quota_id}</span>
          </div>
          <div className="text-white text-sm">{item.project_name}</div>
          <div className="text-slate-400 text-xs">{item.unit}</div>
        </div>
        <button onClick={() => onRemove(item.quota_id)} className="p-2 text-red-400 active:text-red-300">
          <Trash2 size={16} />
        </button>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => onQuantityChange(item.quota_id, Math.max(0.1, item.quantity - 1))}
            className="w-8 h-8 bg-slate-700 rounded-lg text-white text-lg flex items-center justify-center active:bg-slate-600"
          >
            −
          </button>
          <input
            type="number"
            value={item.quantity}
            min="0.1"
            step="0.1"
            onChange={(e) => onQuantityChange(item.quota_id, parseFloat(e.target.value) || 0)}
            className="w-16 bg-slate-700 rounded-lg text-white text-center text-sm py-1"
          />
          <button
            onClick={() => onQuantityChange(item.quota_id, item.quantity + 1)}
            className="w-8 h-8 bg-slate-700 rounded-lg text-white text-lg flex items-center justify-center active:bg-slate-600"
          >
            +
          </button>
        </div>
        <div className="text-right">
          <div className="text-white font-bold">
            ¥{(item.total_cost * item.quantity).toFixed(2)}
          </div>
          <div className="text-slate-400 text-xs">
            ¥{item.total_cost.toFixed(2)} × {item.quantity}
          </div>
        </div>
      </div>
    </div>
  )
}
