import { useState, useEffect } from 'react'
import { Plus, FolderOpen, ChevronRight, Trash2, Loader2, X, FileSpreadsheet } from 'lucide-react'
import * as XLSX from 'xlsx'
import {
  listProjects, getProject, createProject, deleteProject,
  removeQuotaFromProject,
  type Project, type ProjectDetail, type ProjectCreate,
} from '../api/project'
import BottomNav from '../components/BottomNav'

// ---- 项目列表页 ----
function ProjectCard({ project, onClick, onDelete }: { project: Project; onClick: () => void; onDelete: () => void }) {
  const statusColor: Record<string, string> = {
    '进行中': 'bg-blue-600',
    '已完成': 'bg-green-600',
    '已归档': 'bg-slate-600',
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-start justify-between">
        <button onClick={onClick} className="flex-1 text-left" onDoubleClick={undefined}>
          <div className="flex items-center gap-2">
            <FolderOpen size={20} className="text-blue-400" />
            <div>
              <div className="text-white font-medium">{project.name}</div>
              <div className="text-slate-400 text-xs mt-0.5">{project.description || '暂无描述'}</div>
            </div>
          </div>
          <div className="flex items-center gap-3 mt-3 text-xs text-slate-400">
            <span>{project.quota_count} 条定额</span>
            <span className="text-slate-600">·</span>
            <span className="text-blue-400 font-medium">¥{project.total_cost.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</span>
            <span className="text-slate-600">·</span>
            <span className={`px-1.5 py-0.5 rounded text-white text-xs ${statusColor[project.status] || 'bg-slate-600'}`}>
              {project.status}
            </span>
          </div>
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="text-slate-500 hover:text-red-400 p-1"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  )
}

// ---- 项目详情页 ----
function ProjectDetailView({
  projectId,
  onBack,
}: {
  projectId: number
  onBack: () => void
}) {
  const [detail, setDetail] = useState<ProjectDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchDetail = async () => {
    setLoading(true)
    try {
      const d = await getProject(projectId)
      setDetail(d)
    } catch {
      alert('加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDetail() }, [projectId])

  const handleRemove = async (quotaId: string) => {
    if (!confirm('确认移除该定额？')) return
    setDeletingId(quotaId)
    try {
      await removeQuotaFromProject(projectId, quotaId)
      await fetchDetail()
    } catch {
      alert('移除失败')
    } finally {
      setDeletingId(null)
    }
  }

  const handleExport = () => {
    if (!detail || detail.items.length === 0) return

    const totalLabor = detail.items.reduce((s, i) => s + (i.labor_fee ?? 0) * i.quantity, 0)
    const totalMaterial = detail.items.reduce((s, i) => s + (i.material_fee ?? 0) * i.quantity, 0)
    const totalMachinery = detail.items.reduce((s, i) => s + (i.machinery_fee ?? 0) * i.quantity, 0)
    const totalManagement = detail.items.reduce((s, i) => s + (i.management_fee ?? 0) * i.quantity, 0)
    const totalTax = detail.items.reduce((s, i) => s + (i.tax ?? 0) * i.quantity, 0)

    const rows = detail.items.map((item, idx) => ({
      '序号': idx + 1,
      '定额编号': item.quota_id,
      '项目名称': item.project_name || '',
      '分部': item.section || '',
      '计量单位': item.unit || '',
      '数量': item.quantity,
      '人工费单价': item.labor_fee ?? 0,
      '材料费单价': item.material_fee ?? 0,
      '机械费单价': item.machinery_fee ?? 0,
      '管理费单价': item.management_fee ?? 0,
      '增值税单价': item.tax ?? 0,
      '合价': ((item.total_cost ?? 0) * item.quantity).toFixed(2),
    }))

    const summary = [
      {},
      { '序号': '', '定额编号': '', '项目名称': '人工费合计', '合价': totalLabor.toFixed(2) },
      { '序号': '', '定额编号': '', '项目名称': '材料费合计', '合价': totalMaterial.toFixed(2) },
      { '序号': '', '定额编号': '', '项目名称': '机械费合计', '合价': totalMachinery.toFixed(2) },
      { '序号': '', '定额编号': '', '项目名称': '管理费合计', '合价': totalManagement.toFixed(2) },
      { '序号': '', '定额编号': '', '项目名称': '增值税合计', '合价': totalTax.toFixed(2) },
      { '序号': '', '定额编号': '', '项目名称': '总计', '合价': detail.total_cost.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) },
    ]

    const ws = XLSX.utils.json_to_sheet([...rows, ...summary])
    ws['!cols'] = [
      { wch: 6 }, { wch: 15 }, { wch: 40 }, { wch: 22 }, { wch: 8 },
      { wch: 8 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 14 },
    ]

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '项目预算书')
    const ts = new Date()
    const timestamp = `${ts.getFullYear()}${String(ts.getMonth()+1).padStart(2,'0')}${String(ts.getDate()).padStart(2,'0')}`
    XLSX.writeFile(wb, `${detail.name}_${timestamp}.xlsx`)
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center pt-20">
        <Loader2 size={32} className="animate-spin text-blue-400" />
      </div>
    )
  }

  if (!detail) return null

  const grandTotal = detail.total_cost

  return (
    <div className="flex-1 pb-24">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800 flex items-center gap-3">
        <button onClick={onBack} className="text-slate-400 hover:text-white">
          <ChevronRight size={20} className="rotate-180" />
        </button>
        <div className="flex-1">
          <h1 className="text-white text-lg font-bold">{detail.name}</h1>
          <div className="text-slate-400 text-xs mt-0.5">
            {detail.quota_count} 条定额 · 共 ¥{grandTotal.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
          </div>
        </div>
        {detail.items.length > 0 && (
          <button
            onClick={handleExport}
            className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-2 rounded-lg"
          >
            <FileSpreadsheet size={14} />
            导出 Excel
          </button>
        )}
      </div>

      {/* Project info */}
      <div className="px-4 py-3">
        <div className="text-slate-400 text-xs space-y-1">
          {detail.region && <div>地区：{detail.region}</div>}
          {detail.budget_period && <div>编制期：{detail.budget_period}</div>}
          {detail.description && <div className="text-slate-300 mt-1">{detail.description}</div>}
        </div>
      </div>

      {/* Quota items */}
      {detail.items.length === 0 ? (
        <div className="px-4 text-center text-slate-500 text-sm py-12">
          暂无定额，请从搜索页添加
        </div>
      ) : (
        <div className="px-4 space-y-2">
          {detail.items.map((item) => (
            <div key={item.quota_id} className="bg-slate-800 rounded-xl p-3 border border-slate-700">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-mono text-sm">{item.quota_id}</span>
                    <span className="text-slate-400 text-xs">× {item.quantity}</span>
                  </div>
                  <div className="text-slate-400 text-xs mt-1">{item.project_name || item.section}</div>
                  <div className="text-slate-500 text-xs mt-0.5">{item.unit || ''}</div>
                </div>
                <div className="text-right">
                  <div className="text-blue-400 font-medium text-sm">
                    ¥{((item.total_cost ?? 0) * item.quantity).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
                  </div>
                  <button
                    onClick={() => handleRemove(item.quota_id)}
                    disabled={deletingId === item.quota_id}
                    className="text-slate-500 hover:text-red-400 text-xs mt-1"
                  >
                    {deletingId === item.quota_id ? '...' : '移除'}
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* 合计栏 */}
          <div className="bg-slate-700/50 rounded-xl p-3 mt-3">
            <div className="text-slate-400 text-xs space-y-1">
              <div className="flex justify-between">
                <span>人工费</span><span className="text-white">¥{detail.items.reduce((s,i) => s+(i.labor_fee??0)*i.quantity,0).toLocaleString('zh-CN',{minimumFractionDigits:2})}</span>
              </div>
              <div className="flex justify-between">
                <span>材料费</span><span className="text-white">¥{detail.items.reduce((s,i) => s+(i.material_fee??0)*i.quantity,0).toLocaleString('zh-CN',{minimumFractionDigits:2})}</span>
              </div>
              <div className="flex justify-between">
                <span>机械费</span><span className="text-white">¥{detail.items.reduce((s,i) => s+(i.machinery_fee??0)*i.quantity,0).toLocaleString('zh-CN',{minimumFractionDigits:2})}</span>
              </div>
              <div className="flex justify-between">
                <span>管理费</span><span className="text-white">¥{detail.items.reduce((s,i) => s+(i.management_fee??0)*i.quantity,0).toLocaleString('zh-CN',{minimumFractionDigits:2})}</span>
              </div>
              <div className="flex justify-between">
                <span>增值税</span><span className="text-white">¥{detail.items.reduce((s,i) => s+(i.tax??0)*i.quantity,0).toLocaleString('zh-CN',{minimumFractionDigits:2})}</span>
              </div>
              <div className="flex justify-between font-medium border-t border-slate-600 pt-1 mt-1">
                <span className="text-slate-300">总计</span>
                <span className="text-blue-400 font-bold">¥{grandTotal.toLocaleString('zh-CN',{minimumFractionDigits:2})}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ---- 主页面 ----
export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  // Create form state
  const [form, setForm] = useState<ProjectCreate>({ name: '', region: '武汉市', description: '' })
  const [creating, setCreating] = useState(false)

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const data = await listProjects()
      setProjects(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProjects() }, [])

  const handleCreate = async () => {
    if (!form.name.trim()) { alert('请输入项目名称'); return }
    setCreating(true)
    try {
      await createProject(form)
      setShowCreate(false)
      setForm({ name: '', region: '武汉市', description: '' })
      await fetchProjects()
    } catch {
      alert('创建失败')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确认删除该项目？')) return
    try {
      await deleteProject(id)
      setProjects(projects => projects.filter(p => p.id !== id))
    } catch {
      alert('删除失败')
    }
  }

  // 如果选中了项目，显示详情
  if (selectedId !== null) {
    return (
      <div className="min-h-screen bg-slate-900">
        <ProjectDetailView projectId={selectedId} onBack={() => setSelectedId(null)} />
        <BottomNav />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <h1 className="text-white text-xl font-bold">项目预算</h1>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white text-xs px-3 py-2 rounded-lg"
          >
            <Plus size={14} />
            新建项目
          </button>
        </div>
      </div>

      {/* Project list */}
      {loading ? (
        <div className="flex items-center justify-center pt-20">
          <Loader2 size={32} className="animate-spin text-blue-400" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center text-slate-500 text-sm pt-16">
          <FolderOpen size={40} className="mx-auto mb-3 opacity-40" />
          <div>暂无项目</div>
          <div className="text-xs mt-1">点击右上角新建项目</div>
        </div>
      ) : (
        <div className="px-4 pt-4 space-y-3">
          {projects.map((p) => (
            <ProjectCard
              key={p.id}
              project={p}
              onClick={() => setSelectedId(p.id)}
              onDelete={() => handleDelete(p.id)}
            />
          ))}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-end justify-center">
          <div className="bg-slate-800 rounded-t-2xl w-full max-w-md px-4 pt-4 pb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-bold">新建项目</h2>
              <button onClick={() => setShowCreate(false)} className="text-slate-400">
                <X size={20} />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">项目名称 *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="如：XX小区园林景观工程"
                  className="w-full bg-slate-700 text-white text-sm rounded-lg px-3 py-2.5 border border-slate-600 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">地区</label>
                <input
                  value={form.region}
                  onChange={(e) => setForm({ ...form, region: e.target.value })}
                  placeholder="武汉市"
                  className="w-full bg-slate-700 text-white text-sm rounded-lg px-3 py-2.5 border border-slate-600 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">描述</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="项目简要描述（可选）"
                  rows={2}
                  className="w-full bg-slate-700 text-white text-sm rounded-lg px-3 py-2.5 border border-slate-600 focus:border-blue-500 resize-none"
                />
              </div>
              <button
                onClick={handleCreate}
                disabled={creating}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded-xl py-3 text-sm font-medium flex items-center justify-center gap-2"
              >
                {creating ? <Loader2 size={16} className="animate-spin" /> : null}
                {creating ? '创建中...' : '创建项目'}
              </button>
            </div>
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  )
}
