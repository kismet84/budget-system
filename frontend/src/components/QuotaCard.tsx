import { ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { QuotaResult } from '../types/quota'

interface Props {
  quota: QuotaResult
  rank: number
  cachedResults: QuotaResult[]
}

export default function QuotaCard({ quota, rank, cachedResults }: Props) {
  const navigate = useNavigate()

  const handleClick = () => {
    // 通过 sessionStorage 传递数据，避免 URL 参数过长
    sessionStorage.setItem('quota-detail', JSON.stringify(quota))
    sessionStorage.setItem('quota-results', JSON.stringify(cachedResults))
    navigate(`/detail/${quota.quota_id}`)
  }

  const formatFee = (v: number | null | undefined, unit = '元') =>
    v != null ? `${v.toFixed(2)}${unit}` : '—'

  return (
    <div
      onClick={handleClick}
      className="bg-slate-800 rounded-xl p-4 border border-slate-700 cursor-pointer active:bg-slate-700 transition-colors"
    >
      {/* 第一行：编号 + 推荐 + 项目名称 + 总价/单位 */}
      <div className="flex items-start justify-between min-w-0">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <span className="font-mono text-blue-400 text-sm font-semibold shrink-0">{quota.quota_id}</span>
          {rank === 0 && (
            <span className="text-xs bg-green-600 text-white px-2 py-0.5 rounded-full shrink-0">推荐</span>
          )}
          <span className="text-white font-medium text-sm truncate min-w-0">{quota.project_name}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <span className="text-white font-bold text-lg">¥{quota.total_cost.toFixed(2)}</span>
          <span className="text-slate-400 text-xs">/{quota.unit}</span>
        </div>
        <ChevronRight size={18} className="text-slate-500 mt-0.5 ml-1 shrink-0" />
      </div>

      {/* 第二行：分类路径 */}
      <div className="text-slate-400 text-xs mt-0.5">分类路径：{quota.section}</div>

      {/* 第三行：工作内容 */}
      {quota.work_content && (
        <div className="text-slate-300 text-xs mt-0.5 truncate">{quota.work_content}</div>
      )}

      {/* 第四行：费用明细 */}
      <div className="text-slate-400 text-xs mt-0.5">
        <span>费用明细：</span>
        <span>人工费 {formatFee(quota.labor_fee)}</span>
        <span className="text-slate-600 mx-1">|</span>
        <span>材料费 {formatFee(quota.material_fee)}</span>
        <span className="text-slate-600 mx-1">|</span>
        <span>机械费 {formatFee(quota.machinery_fee)}</span>
        <span className="text-slate-600 mx-1">|</span>
        <span>管理费 {formatFee(quota.management_fee)}</span>
        <span className="text-slate-600 mx-1">|</span>
        <span>增值税 {formatFee(quota.tax)}</span>
      </div>
    </div>
  )
}
