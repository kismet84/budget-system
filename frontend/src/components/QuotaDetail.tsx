import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { Quota } from '../types/quota'

interface Props {
  quota: Quota
}

export default function QuotaDetail({ quota }: Props) {
  const navigate = useNavigate()

  const formatFee = (v: number | null | undefined) =>
    v != null ? `¥${v.toFixed(2)}` : '—'

  return (
    <div className="min-h-screen bg-slate-900 pb-24">
      {/* Header */}
      <div className="bg-slate-800 p-4 flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <ArrowLeft className="text-white" size={24} />
        </button>
        <span className="text-white font-medium">定额详情</span>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title Section */}
        <div className="bg-slate-800 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-3 mb-3">
            <span className="bg-blue-600 text-white text-lg px-4 py-1 rounded-full font-bold">
              {quota.quota_id}
            </span>
          </div>
          <h1 className="text-white text-2xl font-bold mb-2">{quota.project_name}</h1>
          <p className="text-slate-400 text-sm">{quota.section}</p>
        </div>

        {/* Unit */}
        <div className="bg-slate-800 rounded-xl p-4 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">计量单位</span>
            <span className="text-white font-medium text-lg">{quota.unit}</span>
          </div>
        </div>

        {/* Cost Details */}
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-slate-700">
            <h2 className="text-white font-semibold text-lg">费用明细</h2>
          </div>
          <div className="divide-y divide-slate-700">
            <div className="p-4 flex justify-between items-center">
              <span className="text-slate-400">全费用</span>
              <span className="text-green-400 font-bold text-xl">
                {formatFee(quota.total_cost)}
              </span>
            </div>
            <div className="p-4 flex justify-between items-center">
              <span className="text-slate-400">人工费</span>
              <span className="text-white font-medium">{formatFee(quota.labor_fee)}</span>
            </div>
            <div className="p-4 flex justify-between items-center">
              <span className="text-slate-400">材料费</span>
              <span className="text-white font-medium">{formatFee(quota.material_fee)}</span>
            </div>
            <div className="p-4 flex justify-between items-center">
              <span className="text-slate-400">机械费</span>
              <span className="text-white font-medium">{formatFee(quota.machinery_fee)}</span>
            </div>
            <div className="p-4 flex justify-between items-center">
              <span className="text-slate-400">管理费</span>
              <span className="text-white font-medium">{formatFee(quota.management_fee)}</span>
            </div>
            <div className="p-4 flex justify-between items-center">
              <span className="text-slate-400">增值税</span>
              <span className="text-white font-medium">{formatFee(quota.tax)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Button */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-slate-900 border-t border-slate-800">
        <button
          onClick={() => navigate('/cart')}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-4 rounded-xl transition-colors"
        >
          选用此定额
        </button>
      </div>
    </div>
  )
}
