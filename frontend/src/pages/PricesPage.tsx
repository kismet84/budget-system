import { useState, useEffect, useCallback } from 'react'
import { Search, Plus, X, Pencil, Trash2, Loader2, ChevronLeft, ChevronRight, TrendingUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { listPrices, createPrice, updatePrice, deletePrice, getPriceHistory, MaterialPrice, MaterialPriceCreate, PriceHistoryPoint } from '../api/price'
import BottomNav from '../components/BottomNav'

const PRICE_TYPES = ['信息价', '企业价']
const REGIONS = ['武汉市', '黄石市', '鄂州市', '黄冈市', '荆州市', '宜昌市', '襄阳市', '十堰市', '荆门市', '孝感市', '咸宁市', '随州市', '恩施州', '仙桃市', '潜江市', '天门市', '神农架林区']

function isPriceExpired(publicationDate: string): boolean {
  const pubDate = new Date(publicationDate)
  const now = new Date()
  const diffDays = (now.getTime() - pubDate.getTime()) / (1000 * 60 * 60 * 24)
  return diffDays > 30
}

export default function PricesPage() {
  const [prices, setPrices] = useState<MaterialPrice[]>([])
  const [loading, setLoading] = useState(true)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterRegion, setFilterRegion] = useState('')
  const [page, setPage] = useState(0)
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [selectedPrice, setSelectedPrice] = useState<MaterialPrice | null>(null)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [chartPrice, setChartPrice] = useState<MaterialPrice | null>(null)
  const [chartData, setChartData] = useState<PriceHistoryPoint[]>([])
  const [chartLoading, setChartLoading] = useState(false)

  const limit = 20

  const fetchPrices = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listPrices({
        skip: page * limit,
        limit,
        name: searchKeyword || undefined,
        price_type: filterType || undefined,
        region: filterRegion || undefined,
      })
      setPrices(data)
    } catch (err) {
      console.error('Failed to fetch prices:', err)
    } finally {
      setLoading(false)
    }
  }, [page, searchKeyword, filterType, filterRegion])

  useEffect(() => {
    fetchPrices()
  }, [fetchPrices])

  const handleSearch = () => {
    setPage(0)
    fetchPrices()
  }

  const handleCreate = () => {
    setModalMode('create')
    setSelectedPrice(null)
    setShowModal(true)
  }

  const handleEdit = (price: MaterialPrice) => {
    setModalMode('edit')
    setSelectedPrice(price)
    setShowModal(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这条价格记录吗？')) return
    setDeletingId(id)
    try {
      await deletePrice(id)
      fetchPrices()
    } catch (err) {
      console.error('Failed to delete:', err)
      alert('删除失败')
    } finally {
      setDeletingId(null)
    }
  }

  const handleSave = async (formData: MaterialPriceCreate) => {
    setSaving(true)
    try {
      if (modalMode === 'create') {
        await createPrice(formData)
      } else if (selectedPrice) {
        await updatePrice(selectedPrice.id, formData)
      }
      setShowModal(false)
      fetchPrices()
    } catch (err) {
      console.error('Failed to save:', err)
      alert('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleShowChart = async (price: MaterialPrice) => {
    setChartPrice(price)
    setChartLoading(true)
    setChartData([])
    try {
      const data = await getPriceHistory(price.id)
      setChartData(data)
    } catch {
      alert('加载历史走势失败')
    } finally {
      setChartLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-white text-xl font-bold">材料价格</h1>
          <button
            onClick={handleCreate}
            className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-3 py-1.5 text-sm flex items-center gap-1"
          >
            <Plus size={16} />
            新增
          </button>
        </div>

        {/* Search */}
        <div className="flex gap-2 mb-3">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索材料名称..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-sm"
          >
            搜索
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <select
            value={filterType}
            onChange={(e) => { setFilterType(e.target.value); setPage(0); }}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">全部类型</option>
            {PRICE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select
            value={filterRegion}
            onChange={(e) => { setFilterRegion(e.target.value); setPage(0); }}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">全部地区</option>
            {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="px-4 py-3">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={24} className="animate-spin text-slate-400" />
          </div>
        ) : prices.length === 0 ? (
          <div className="text-center py-20 text-slate-500 text-sm">暂无数据</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 text-left border-b border-slate-700">
                    <th className="pb-2 font-medium">材料名称</th>
                    <th className="pb-2 font-medium">规格</th>
                    <th className="pb-2 font-medium">单位</th>
                    <th className="pb-2 font-medium text-right">单价</th>
                    <th className="pb-2 font-medium">类型</th>
                    <th className="pb-2 font-medium">地区</th>
                    <th className="pb-2 font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {prices.map((price) => {
                    const expired = isPriceExpired(price.publication_date)
                    return (
                    <tr key={price.id} className={`border-b border-slate-800 ${expired ? 'text-red-400' : 'text-white'}`}>
                      <td className="py-2.5 pr-3 max-w-[120px] truncate">
                        {price.name}
                        {expired && (
                          <span className="ml-1.5 text-xs bg-red-900 text-red-300 px-1 py-0.5 rounded">
                            已过期
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 pr-3 text-slate-400 max-w-[100px] truncate">{price.specification}</td>
                      <td className="py-2.5 pr-3 text-slate-400">{price.unit}</td>
                      <td className="py-2.5 pr-3 text-right text-blue-400">¥{price.unit_price.toFixed(2)}</td>
                      <td className="py-2.5 pr-3">
                        <span className={`text-xs px-1.5 py-0.5 rounded ${price.price_type === '信息价' ? 'bg-blue-900 text-blue-300' : 'bg-green-900 text-green-300'}`}>
                          {price.price_type}
                        </span>
                      </td>
                      <td className="py-2.5 pr-3 text-slate-400">{price.region}</td>
                      <td className="py-2.5">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleShowChart(price)}
                            title="历史走势"
                            className="text-slate-400 hover:text-blue-400 p-1"
                          >
                            <TrendingUp size={14} />
                          </button>
                          <button
                            onClick={() => handleEdit(price)}
                            className="text-slate-400 hover:text-white p-1"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(price.id)}
                            disabled={deletingId === price.id}
                            className="text-slate-400 hover:text-red-400 p-1 disabled:opacity-50"
                          >
                            {deletingId === price.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-center gap-4 mt-4">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 disabled:opacity-30 hover:text-white"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="text-sm text-slate-400">第 {page + 1} 页</span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={prices.length < limit}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 disabled:opacity-30 hover:text-white"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <PriceModal
          mode={modalMode}
          price={selectedPrice}
          onSave={handleSave}
          onClose={() => setShowModal(false)}
          saving={saving}
        />
      )}

      {/* Price History Chart Modal */}
      {chartPrice && (
        <div
          className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
          onClick={(e) => { if (e.target === e.currentTarget) setChartPrice(null) }}
        >
          <div className="bg-slate-800 rounded-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
              <div>
                <h2 className="text-white font-medium">价格走势</h2>
                <div className="text-slate-400 text-xs mt-0.5">{chartPrice.name} · {chartPrice.region} · {chartPrice.price_type}</div>
              </div>
              <button onClick={() => setChartPrice(null)} className="text-slate-400 hover:text-white">
                <X size={20} />
              </button>
            </div>
            <div className="p-4">
              {chartLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 size={24} className="animate-spin text-slate-400" />
                </div>
              ) : chartData.length === 0 ? (
                <div className="text-center text-slate-500 text-sm py-16">暂无历史数据</div>
              ) : (
                <>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="date"
                          tick={{ fill: '#94a3b8', fontSize: 11 }}
                          tickFormatter={(v: string) => v.slice(0, 7)}
                        />
                        <YAxis
                          tick={{ fill: '#94a3b8', fontSize: 11 }}
                          tickFormatter={(v: number) => v.toFixed(0)}
                          width={50}
                        />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: 8, color: '#e2e8f0' }}
                          formatter={(value) => [`¥${Number(value).toFixed(2)}`, '单价']}
                          labelFormatter={(label) => `日期：${label}`}
                        />
                        <Line
                          type="monotone"
                          dataKey="price"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={{ r: 3, fill: '#3b82f6' }}
                          activeDot={{ r: 5 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-3 text-xs text-slate-400">
                    共 {chartData.length} 个月数据 · 最高 ¥{Math.max(...chartData.map(d => d.price)).toFixed(2)} · 最低 ¥{Math.min(...chartData.map(d => d.price)).toFixed(2)}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  )
}

interface PriceModalProps {
  mode: 'create' | 'edit'
  price: MaterialPrice | null
  onSave: (data: MaterialPriceCreate) => void
  onClose: () => void
  saving: boolean
}

function PriceModal({ mode, price, onSave, onClose, saving }: PriceModalProps) {
  const [form, setForm] = useState<MaterialPriceCreate>({
    name: price?.name ?? '',
    specification: price?.specification ?? '',
    unit: price?.unit ?? '',
    unit_price: price?.unit_price ?? 0,
    price_type: price?.price_type ?? '信息价',
    region: price?.region ?? '武汉市',
    publication_date: price?.publication_date ? price.publication_date.split('T')[0] : new Date().toISOString().split('T')[0],
    source: price?.source ?? '',
    is_active: price?.is_active ?? true,
    remarks: price?.remarks ?? '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.unit || form.unit_price <= 0) {
      alert('请填写必填项：名称、单位、单价')
      return
    }
    onSave(form)
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-white font-medium">{mode === 'create' ? '新增价格' : '编辑价格'}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-slate-400 text-xs mb-1">材料名称 *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="例如：热轧碳素结构钢圆钢"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-xs mb-1">规格型号</label>
            <input
              type="text"
              value={form.specification}
              onChange={(e) => setForm({ ...form, specification: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="例如：Φ9-10mm HPB300"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 text-xs mb-1">单位 *</label>
              <input
                type="text"
                value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                placeholder="例如：t"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-xs mb-1">单价（元）*</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.unit_price}
                onChange={(e) => setForm({ ...form, unit_price: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 text-xs mb-1">价格类型</label>
              <select
                value={form.price_type}
                onChange={(e) => setForm({ ...form, price_type: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              >
                {PRICE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-slate-400 text-xs mb-1">地区</label>
              <select
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              >
                {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 text-xs mb-1">发布日期</label>
            <input
              type="date"
              value={form.publication_date}
              onChange={(e) => setForm({ ...form, publication_date: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-xs mb-1">来源</label>
            <input
              type="text"
              value={form.source}
              onChange={(e) => setForm({ ...form, source: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="例如：湖北省建设工程造价信息网"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="rounded bg-slate-700 border-slate-600"
            />
            <label htmlFor="is_active" className="text-slate-400 text-sm">是否有效</label>
          </div>

          <div>
            <label className="block text-slate-400 text-xs mb-1">备注</label>
            <textarea
              value={form.remarks}
              onChange={(e) => setForm({ ...form, remarks: e.target.value })}
              rows={2}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-slate-700 hover:bg-slate-600 text-white rounded-lg py-2.5 text-sm"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded-lg py-2.5 text-sm flex items-center justify-center gap-2"
            >
              {saving && <Loader2 size={14} className="animate-spin" />}
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
