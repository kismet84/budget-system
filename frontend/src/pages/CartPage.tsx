import { FileText } from 'lucide-react'
import { useCartStore } from '../store/cartStore'
import CartItem from '../components/CartItem'
import BottomNav from '../components/BottomNav'

export default function CartPage() {
  const items = useCartStore((s) => s.items)
  const removeItem = useCartStore((s) => s.removeItem)
  const updateQuantity = useCartStore((s) => s.updateQuantity)
  const totalCost = useCartStore((s) => s.totalCost())
  const totalLabor = useCartStore((s) => s.totalLabor())
  const totalMaterial = useCartStore((s) => s.totalMaterial())
  const totalMachinery = useCartStore((s) => s.totalMachinery())
  const totalManagement = useCartStore((s) => s.totalManagement())
  const totalTax = useCartStore((s) => s.totalTax())

  return (
    <div className="min-h-screen bg-slate-900 pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800">
        <h1 className="text-white text-xl font-bold">已选定额</h1>
        {items.length > 0 && (
          <div className="text-slate-400 text-sm mt-1">共 {items.length} 项</div>
        )}
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center pt-20 text-slate-500">
          <FileText size={48} className="mb-3 opacity-50" />
          <div className="text-sm">清单为空</div>
          <div className="text-xs mt-1">从搜索页选用定额</div>
        </div>
      ) : (
        <div className="px-4 pt-4 space-y-3">
          {items.map((item) => (
            <CartItem
              key={item.quota_id}
              item={item}
              onRemove={removeItem}
              onQuantityChange={updateQuantity}
            />
          ))}
        </div>
      )}

      {/* Summary */}
      {items.length > 0 && (
        <div className="fixed bottom-20 left-0 right-0 bg-slate-800 border-t border-slate-700 px-4 py-3 z-10">
          <div className="space-y-1 text-xs text-slate-400 mb-2">
            <div className="flex justify-between">
              <span>人工费</span><span className="text-white">¥{totalLabor.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>材料费</span><span className="text-white">¥{totalMaterial.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>机械费</span><span className="text-white">¥{totalMachinery.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>管理费</span><span className="text-white">¥{totalManagement.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span>增值税</span><span className="text-white">¥{totalTax.toFixed(2)}</span>
            </div>
            <div className="flex justify-between font-medium text-white text-sm pt-1 border-t border-slate-700 mt-1">
              <span>合计</span><span className="text-blue-400 font-bold">¥{totalCost.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Generate Button */}
      {items.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 px-4 pb-6 pt-3 bg-slate-900">
          <button className="w-full bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-xl py-4 text-base font-medium transition-colors">
            生成预算书
          </button>
        </div>
      )}

      <BottomNav />
    </div>
  )
}
