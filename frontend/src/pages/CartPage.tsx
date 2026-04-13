import { useState } from 'react'
import { FileText, Download, Loader2 } from 'lucide-react'
import { useCartStore } from '../store/cartStore'
import CartItem from '../components/CartItem'
import BottomNav from '../components/BottomNav'
import * as XLSX from 'xlsx'

export default function CartPage() {
  const [isExporting, setIsExporting] = useState(false)
  const items = useCartStore((s) => s.items)
  const removeItem = useCartStore((s) => s.removeItem)
  const updateQuantity = useCartStore((s) => s.updateQuantity)
  const totalCost = useCartStore((s) => s.totalCost())
  const totalLabor = useCartStore((s) => s.totalLabor())
  const totalMaterial = useCartStore((s) => s.totalMaterial())
  const totalMachinery = useCartStore((s) => s.totalMachinery())
  const totalManagement = useCartStore((s) => s.totalManagement())
  const totalTax = useCartStore((s) => s.totalTax())

  const handleGenerateBudget = () => {
    if (items.length === 0) return
    setIsExporting(true)

    try {
      // Prepare data for Excel
      const exportData = items.map((item, index) => ({
        '序号': index + 1,
        '定额编号': item.quota_id,
        '项目名称': item.project_name,
        '分部': item.section,
        '计量单位': item.unit,
        '数量': item.quantity,
        '人工费单价': item.labor_fee ?? 0,
        '材料费单价': item.material_fee ?? 0,
        '机械费单价': item.machinery_fee ?? 0,
        '管理费单价': item.management_fee ?? 0,
        '增值税单价': item.tax ?? 0,
        '合价': (item.total_cost ?? 0) * item.quantity,
      }))

      // Add summary rows
      const summaryRows = [
        {},
        { '序号': '', '定额编号': '', '项目名称': '人工费合计', '合价': totalLabor },
        { '序号': '', '定额编号': '', '项目名称': '材料费合计', '合价': totalMaterial },
        { '序号': '', '定额编号': '', '项目名称': '机械费合计', '合价': totalMachinery },
        { '序号': '', '定额编号': '', '项目名称': '管理费合计', '合价': totalManagement },
        { '序号': '', '定额编号': '', '项目名称': '增值税合计', '合价': totalTax },
        { '序号': '', '定额编号': '', '项目名称': '总计', '合价': totalCost },
      ]

      const data = [...exportData, ...summaryRows]

      // Create workbook and worksheet
      const ws = XLSX.utils.json_to_sheet(data)
      
      // Set column widths
      ws['!cols'] = [
        { wch: 6 },   // 序号
        { wch: 15 },  // 定额编号
        { wch: 40 },  // 项目名称
        { wch: 20 },  // 分部
        { wch: 8 },   // 计量单位
        { wch: 8 },   // 数量
        { wch: 12 },  // 人工费单价
        { wch: 12 },  // 材料费单价
        { wch: 12 },  // 机械费单价
        { wch: 12 },  // 管理费单价
        { wch: 12 },  // 增值税单价
        { wch: 14 },  // 合价
      ]

      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '预算书')

      // Generate filename with timestamp
      const now = new Date()
      const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`
      const filename = `预算书_${timestamp}.xlsx`

      // Download
      XLSX.writeFile(wb, filename)
    } catch (error) {
      console.error('Export error:', error)
      alert('导出失败，请重试')
    } finally {
      setIsExporting(false)
    }
  }

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
          <button
            onClick={handleGenerateBudget}
            disabled={isExporting}
            className="w-full bg-blue-600 hover:bg-blue-500 active:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white rounded-xl py-4 text-base font-medium transition-colors flex items-center justify-center gap-2"
          >
            {isExporting ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                导出中...
              </>
            ) : (
              <>
                <Download size={18} />
                生成预算书
              </>
            )}
          </button>
        </div>
      )}

      <BottomNav />
    </div>
  )
}
