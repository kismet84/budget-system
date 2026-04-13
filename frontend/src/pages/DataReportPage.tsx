import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, AlertTriangle, CheckCircle, Database, BarChart2, Clock } from 'lucide-react'
import axios from 'axios'

interface DataReport {
  coverage: {
    quota_total: number
    material_price_total: number
  }
  quota_missing_fields: Record<string, number>
  quota_section_breakdown: Array<{ section: string; count: number }>
  material_region_breakdown: Array<{ region: string; count: number }>
  material_month_breakdown: Array<{ month: string; count: number }>
  material_price_type_breakdown: Array<{ price_type: string; count: number }>
  price_expiry: {
    active_total: number
    expiring_soon: number
    threshold_days: number
  }
  generated_at: string
}

const api = axios.create({
  baseURL: '',
  timeout: 15000,
})

export default function DataReportPage() {
  const [report, setReport] = useState<DataReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchReport = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get<DataReport>('/api/v1/admin/report')
      setReport(res.data)
    } catch (err) {
      console.error('Failed to fetch report:', err)
      setError('获取报告失败，请检查服务器连接')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReport()
  }, [fetchReport])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw size={32} className="animate-spin text-blue-400 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">正在生成数据质量报告...</p>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle size={32} className="text-red-400 mx-auto mb-3" />
          <p className="text-red-400 text-sm">{error || '获取报告失败'}</p>
          <button
            onClick={fetchReport}
            className="mt-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-sm"
          >
            重试
          </button>
        </div>
      </div>
    )
  }

  const expiringPercent = report.price_expiry.active_total > 0
    ? Math.round((report.price_expiry.expiring_soon / report.price_expiry.active_total) * 100)
    : 0

  return (
    <div className="min-h-screen bg-slate-900 pb-8">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <h1 className="text-white text-xl font-bold">数据质量报告</h1>
          <button
            onClick={fetchReport}
            className="text-slate-400 hover:text-white flex items-center gap-1 text-xs"
          >
            <RefreshCw size={14} />
            刷新
          </button>
        </div>
        <p className="text-slate-500 text-xs mt-1">生成时间：{report.generated_at}</p>
      </div>

      <div className="px-4 py-4 space-y-4">

        {/* ── 1. 数据覆盖率 ─────────────────────────────── */}
        <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h2 className="text-white font-medium mb-3 flex items-center gap-2">
            <Database size={16} className="text-blue-400" />
            数据覆盖率
          </h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-400">{report.coverage.quota_total.toLocaleString()}</div>
              <div className="text-slate-400 text-xs mt-1">定额总数</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-400">{report.coverage.material_price_total.toLocaleString()}</div>
              <div className="text-slate-400 text-xs mt-1">材料价格记录</div>
            </div>
          </div>
        </section>

        {/* ── 2. 定额缺失字段 ───────────────────────────── */}
        <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h2 className="text-white font-medium mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-400" />
            定额缺失字段
          </h2>
          {Object.keys(report.quota_missing_fields).length === 0 ? (
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <CheckCircle size={14} />
              所有关键字段均已填充
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(report.quota_missing_fields).map(([field, count]) => (
                <div key={field} className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">{field}</span>
                  <span className={count > 0 ? 'text-red-400' : 'text-slate-500'}>
                    {count > 0 ? `${count} 条缺失` : '完整'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ── 3. 定额分部统计 ───────────────────────────── */}
        <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h2 className="text-white font-medium mb-3 flex items-center gap-2">
            <BarChart2 size={16} className="text-purple-400" />
            定额分部统计
          </h2>
          {report.quota_section_breakdown.length === 0 ? (
            <p className="text-slate-500 text-sm">暂无数据</p>
          ) : (
            <div className="space-y-2">
              {report.quota_section_breakdown.map((item) => {
                const percent = report.coverage.quota_total > 0
                  ? Math.round((item.count / report.coverage.quota_total) * 100)
                  : 0
                return (
                  <div key={item.section} className="flex items-center gap-3">
                    <div className="w-28 text-slate-300 text-xs truncate">{item.section}</div>
                    <div className="flex-1 bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-purple-500 h-2 rounded-full transition-all"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <div className="text-right w-20 text-slate-400 text-xs">
                      {item.count} ({percent}%)
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        {/* ── 4. 材料价格统计（按地区）───────────────────── */}
        <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h2 className="text-white font-medium mb-3 flex items-center gap-2">
            <BarChart2 size={16} className="text-green-400" />
            材料价格 — 按地区
          </h2>
          {report.material_region_breakdown.length === 0 ? (
            <p className="text-slate-500 text-sm">暂无数据</p>
          ) : (
            <div className="space-y-2">
              {report.material_region_breakdown.map((item) => {
                const percent = report.coverage.material_price_total > 0
                  ? Math.round((item.count / report.coverage.material_price_total) * 100)
                  : 0
                return (
                  <div key={item.region} className="flex items-center gap-3">
                    <div className="w-20 text-slate-300 text-xs truncate">{item.region}</div>
                    <div className="flex-1 bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full transition-all"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                    <div className="text-right w-20 text-slate-400 text-xs">
                      {item.count}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>

        {/* ── 5. 材料价格统计（按月份）───────────────────── */}
        <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h2 className="text-white font-medium mb-3 flex items-center gap-2">
            <Clock size={16} className="text-cyan-400" />
            材料价格 — 按月份
          </h2>
          {report.material_month_breakdown.length === 0 ? (
            <p className="text-slate-500 text-sm">暂无数据</p>
          ) : (
            <div className="space-y-2">
              {report.material_month_breakdown.map((item) => (
                <div key={item.month} className="flex items-center justify-between text-sm">
                  <span className="text-slate-300 text-xs">{item.month}</span>
                  <span className="text-cyan-400 text-xs">{item.count} 条</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ── 6. 价格有效期 ─────────────────────────────── */}
        <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h2 className="text-white font-medium mb-3 flex items-center gap-2">
            <Clock size={16} className={expiringPercent > 50 ? 'text-red-400' : 'text-blue-400'} />
            价格有效期
            <span className="text-xs text-slate-500 ml-1">（超过 {report.price_expiry.threshold_days} 天未更新）</span>
          </h2>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <div className="text-xl font-bold text-white">{report.price_expiry.active_total.toLocaleString()}</div>
              <div className="text-slate-400 text-xs mt-1">有效价格</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <div className={`text-xl font-bold ${report.price_expiry.expiring_soon > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {report.price_expiry.expiring_soon.toLocaleString()}
              </div>
              <div className="text-slate-400 text-xs mt-1">需更新</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <div className={`text-xl font-bold ${expiringPercent > 50 ? 'text-red-400' : 'text-green-400'}`}>
                {expiringPercent}%
              </div>
              <div className="text-slate-400 text-xs mt-1">过期率</div>
            </div>
          </div>
          {report.price_expiry.expiring_soon > 0 && (
            <div className="bg-red-900/30 border border-red-800 rounded-lg p-3 flex items-start gap-2">
              <AlertTriangle size={14} className="text-red-400 mt-0.5 flex-shrink-0" />
              <p className="text-red-300 text-xs">
                有 <strong>{report.price_expiry.expiring_soon}</strong> 条价格记录超过 {report.price_expiry.threshold_days} 天未更新，
                请及时补充最新价格信息。
              </p>
            </div>
          )}
          {report.price_expiry.expiring_soon === 0 && (
            <div className="flex items-center gap-2 text-green-400 text-xs">
              <CheckCircle size={12} />
              所有价格均在有效期内
            </div>
          )}
        </section>

        {/* ── 7. 价格类型统计 ───────────────────────────── */}
        {report.material_price_type_breakdown.length > 0 && (
          <section className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h2 className="text-white font-medium mb-3 flex items-center gap-2">
              <BarChart2 size={16} className="text-amber-400" />
              材料价格 — 按类型
            </h2>
            <div className="space-y-2">
              {report.material_price_type_breakdown.map((item) => (
                <div key={item.price_type} className="flex items-center justify-between text-sm">
                  <span className="text-slate-300">{item.price_type}</span>
                  <span className="text-amber-400">{item.count} 条</span>
                </div>
              ))}
            </div>
          </section>
        )}

      </div>
    </div>
  )
}
