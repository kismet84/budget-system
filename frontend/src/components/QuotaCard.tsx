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
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-blue-400 text-sm font-semibold">{quota.quota_id}</span>
            {rank === 0 && (
              <span className="text-xs bg-green-600 text-white px-2 py-0.5 rounded-full">推荐</span>
            )}
          </div>
          <div className="text-white font-medium text-sm">{quota.project_name}</div>
          <div className="text-slate-400 text-xs mt-0.5">{quota.section}</div>
        </div>
        <ChevronRight size={18} className="text-slate-500 mt-1" />
      </div>

      <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
        <div className="text-right">
          <div className="text-white font-bold text-lg">
            ¥{quota.total_cost.toFixed(2)}
          </div>
          <div className="text-slate-400 text-xs">/{quota.unit}</div>
        </div>
        <div className="text-right text-xs text-slate-400 space-y-0.5">
          <div>人工费 {formatFee(quota.labor_fee)}</div>
          <div>材料费 {formatFee(quota.material_fee)}</div>
        </div>
      </div>
    </div>
  )
}
