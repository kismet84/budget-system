import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, CheckCircle2, FolderPlus } from 'lucide-react'
import { useState } from 'react'
import { useCartStore } from '../store/cartStore'
import { addQuotaToProject, listProjects, type Project } from '../api/project'
import type { QuotaResult, CartItem } from '../types/quota'

export default function DetailPage() {
  const navigate = useNavigate()
  useParams<{ quota_id: string }>()
  const addItem = useCartStore((s) => s.addItem)
  const items = useCartStore((s) => s.items)
  const [showProjectPicker, setShowProjectPicker] = useState(false)
  const [projects, setProjects] = useState<Project[]>([])
  const [addingProject, setAddingProject] = useState<number | null>(null)

  let quota: QuotaResult | null = null
  try {
    const raw = sessionStorage.getItem('quota-detail')
    quota = raw ? (JSON.parse(raw) as QuotaResult) : null
  } catch (err) {
    console.warn('[DetailPage] sessionStorage 读取失败:', err)
    quota = null
  }

  if (!quota) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-slate-400">定额数据不存在</div>
      </div>
    )
  }

  const alreadyInCart = items.some((i) => i.quota_id === quota.quota_id)

  const handleOpenProjectPicker = async () => {
    const data = await listProjects()
    setProjects(data)
    setShowProjectPicker(true)
  }

  const handleAddToProject = async (projectId: number) => {
    setAddingProject(projectId)
    try {
      await addQuotaToProject(projectId, quota!.quota_id, 1)
      setShowProjectPicker(false)
      alert('已添加至项目')
    } catch {
      alert('添加失败')
    } finally {
      setAddingProject(null)
    }
  }

  const handleAdd = () => {
    const cartItem: CartItem = {
      quota_id: quota.quota_id,
      project_name: quota.project_name ?? '未命名定额',
      section: quota.section,
      unit: quota.unit,
      quantity: 1,
      total_cost: quota.total_cost,
      labor_fee: quota.labor_fee,
      material_fee: quota.material_fee,
      machinery_fee: quota.machinery_fee,
      management_fee: quota.management_fee,
      tax: quota.tax,
      addedAt: Date.now(),
    }
    addItem(cartItem)
    navigate('/cart')
  }

  const feeRows = [
    { label: '全费用', value: quota.total_cost, unit: '元' },
    { label: '人工费', value: quota.labor_fee, unit: '元' },
    { label: '材料费', value: quota.material_fee, unit: '元' },
    { label: '机械费', value: quota.machinery_fee, unit: '元' },
    { label: '管理费', value: quota.management_fee, unit: '元' },
    { label: '增值税', value: quota.tax, unit: '元' },
  ]

  return (
    <div className="min-h-screen bg-slate-900 pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 flex items-center gap-3 px-4 pt-6 pb-4 border-b border-slate-800">
        <button
          onClick={() => navigate(-1)}
          className="p-2 -ml-2 text-slate-400 active:text-white"
        >
          <ArrowLeft size={22} />
        </button>
        <div>
          <div className="font-mono text-blue-400 text-sm">{quota.quota_id}</div>
          <div className="text-white font-medium text-base leading-tight">{quota.project_name}</div>
        </div>
      </div>

      <div className="px-4 py-4 space-y-4">
        {/* Meta */}
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <div className="text-slate-400 text-xs">{quota.section}</div>
          <div className="text-slate-300 text-sm mt-1">计量单位：{quota.unit}</div>
        </div>

        {/* Fee Table */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-700">
            <span className="text-white font-medium text-sm">费用明细</span>
          </div>
          {feeRows.map(({ label, value, unit }) => (
            <div
              key={label}
              className="flex items-center justify-between px-4 py-3 border-b border-slate-700 last:border-0"
            >
              <span className="text-slate-400 text-sm">{label}</span>
              <span className={`text-sm font-medium ${label === '全费用' ? 'text-white text-base' : 'text-slate-300'}`}>
                {value != null ? `¥${value.toFixed(2)}${unit}` : '—'}
              </span>
            </div>
          ))}
        </div>

        {/* Work Content */}
        {quota.work_content && (
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <div className="text-slate-400 text-xs mb-1">工作内容</div>
            <div className="text-slate-300 text-sm">{quota.work_content}</div>
          </div>
        )}
      </div>

      {/* Fixed Bottom Button */}
      <div className="fixed bottom-0 left-0 right-0 px-4 pb-6 pt-3 bg-gradient-to-t from-slate-900 via-slate-900 to-transparent">
        {alreadyInCart ? (
          <div className="flex items-center justify-center gap-2 bg-slate-700 text-slate-400 rounded-xl py-4 text-sm">
            <CheckCircle2 size={18} />
            已加入清单
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={handleOpenProjectPicker}
              className="flex-1 flex items-center justify-center gap-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-xl py-4 text-sm font-medium"
            >
              <FolderPlus size={16} />
              加入项目
            </button>
            <button
              onClick={handleAdd}
              className="flex-1 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-xl py-4 text-sm font-medium"
            >
              加入清单
            </button>
          </div>
        )}
      </div>

      {/* Project Picker Modal */}
      {showProjectPicker && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-end justify-center">
          <div className="bg-slate-800 rounded-t-2xl w-full max-w-md px-4 pt-4 pb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-bold">加入项目</h2>
              <button onClick={() => setShowProjectPicker(false)} className="text-slate-400">
                ×
              </button>
            </div>
            {projects.length === 0 ? (
              <div className="text-center text-slate-500 text-sm py-6">
                暂无项目，请先在「项目」页面创建
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {projects.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => handleAddToProject(p.id)}
                    disabled={addingProject !== null}
                    className="w-full flex items-center justify-between bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-xl px-4 py-3 text-sm"
                  >
                    <div className="text-left">
                      <div>{p.name}</div>
                      <div className="text-slate-400 text-xs">{p.quota_count} 条定额</div>
                    </div>
                    {addingProject === p.id ? (
                      <span className="text-slate-400 text-xs">添加中...</span>
                    ) : (
                      <span className="text-blue-400 text-xs">添加</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
