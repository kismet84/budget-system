import { useState, useEffect, useRef } from 'react'
import { Upload, FileSpreadsheet, XCircle, AlertCircle, Loader2, RefreshCw, Database } from 'lucide-react'
import { importQuotaExcel, getImportReport, type ImportReport, type ImportReportResponse } from '../api/quotaImport'
import BottomNav from '../components/BottomNav'

export default function AdminQuotaPage() {
  const [report, setReport] = useState<ImportReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    fetchReport()
  }, [])

  const fetchReport = async () => {
    setLoading(true)
    setError('')
    try {
      const data: ImportReportResponse = await getImportReport()
      setReport(data.latest_import)
    } catch {
      setError('获取报告失败，请检查服务器连接')
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = async (file: File | undefined) => {
    if (!file) return
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      setError('仅支持 .xlsx / .xls 格式')
      return
    }
    setImporting(true)
    setError('')
    try {
      const result = await importQuotaExcel(file)
      setReport(result)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '导入失败')
    } finally {
      setImporting(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFileChange(file)
  }

  const sectionColors: Record<string, string> = {
    '园林景观': 'bg-emerald-600',
    '绿化': 'bg-green-600',
    '园路': 'bg-amber-600',
    '措施项目': 'bg-purple-600',
    '装饰工程': 'bg-blue-600',
    '未分类': 'bg-slate-600',
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <h1 className="text-white text-xl font-bold">定额导入</h1>
          <button
            onClick={fetchReport}
            disabled={loading}
            className="text-slate-400 hover:text-white flex items-center gap-1 text-xs"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            刷新
          </button>
        </div>
        <p className="text-slate-400 text-xs mt-1">管理员入口 · Excel 定额文件导入</p>
      </div>

      <div className="px-4 pt-4 space-y-4">
        {/* Upload Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => !importing && fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-colors
            ${dragging ? 'border-blue-400 bg-blue-950/30' : 'border-slate-700 hover:border-slate-500 bg-slate-800/50'}
            ${importing ? 'cursor-not-allowed opacity-60' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={(e) => handleFileChange(e.target.files?.[0])}
          />
          {importing ? (
            <>
              <Loader2 size={40} className="mx-auto text-blue-400 animate-spin mb-3" />
              <p className="text-slate-300 text-sm font-medium">正在解析并导入…</p>
              <p className="text-slate-500 text-xs mt-1">请稍候</p>
            </>
          ) : (
            <>
              <div className="w-14 h-14 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-3">
                <Upload size={28} className="text-blue-400" />
              </div>
              <p className="text-slate-200 text-sm font-medium">点击上传或拖拽文件</p>
              <p className="text-slate-500 text-xs mt-1">支持 .xlsx / .xls 格式</p>
            </>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-950/40 border border-red-800 rounded-xl p-3 flex items-start gap-2">
            <XCircle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Report */}
        {loading ? (
          <div className="flex items-center justify-center py-8 gap-2 text-slate-400 text-sm">
            <Loader2 size={16} className="animate-spin" />
            加载中…
          </div>
        ) : report ? (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-800 rounded-xl p-3 text-center border border-slate-700">
                <div className="text-2xl font-bold text-white">{report.total_rows}</div>
                <div className="text-slate-400 text-xs mt-0.5">总行数</div>
              </div>
              <div className="bg-emerald-950/40 rounded-xl p-3 text-center border border-emerald-800">
                <div className="text-2xl font-bold text-emerald-400">{report.success_count}</div>
                <div className="text-emerald-400/70 text-xs mt-0.5">成功</div>
              </div>
              <div className="bg-red-950/40 rounded-xl p-3 text-center border border-red-800">
                <div className="text-2xl font-bold text-red-400">{report.error_count}</div>
                <div className="text-red-400/70 text-xs mt-0.5">失败</div>
              </div>
            </div>

            {/* File Info */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <FileSpreadsheet size={16} className="text-slate-400" />
                <span className="text-slate-300 text-sm font-medium">{report.filename}</span>
              </div>
              <div className="text-slate-500 text-xs">
                导入时间：{new Date(report.imported_at).toLocaleString('zh-CN')}
              </div>
              {report.skipped_count > 0 && (
                <div className="text-amber-400 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle size={12} />
                  {report.skipped_count} 条已存在（更新了数据）
                </div>
              )}
            </div>

            {/* Section Distribution */}
            {Object.keys(report.section_distribution).length > 0 && (
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center gap-2 mb-3">
                  <Database size={16} className="text-slate-400" />
                  <span className="text-slate-300 text-sm font-medium">分部分布</span>
                </div>
                <div className="space-y-2">
                  {Object.entries(report.section_distribution)
                    .sort((a, b) => b[1] - a[1])
                    .map(([section, count]) => (
                      <div key={section} className="flex items-center gap-3">
                        <div className={`w-1.5 h-4 rounded-full ${sectionColors[section] || 'bg-slate-600'}`} />
                        <span className="text-slate-300 text-sm flex-1">{section}</span>
                        <span className="text-slate-400 text-xs">{count} 条</span>
                      </div>
                    ))
                  }
                </div>
              </div>
            )}

            {/* Errors */}
            {report.errors.length > 0 && (
              <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle size={16} className="text-red-400" />
                  <span className="text-slate-300 text-sm font-medium">错误明细（前10条）</span>
                </div>
                <div className="space-y-2">
                  {report.errors.map((err, i) => (
                    <div key={i} className="text-xs text-slate-400 bg-slate-900 rounded-lg p-2 font-mono">
                      {err.row ? `行${err.row}` : ''} {err.quota_id ? `[${err.quota_id}]` : ''} {err.error}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : !error ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileSpreadsheet size={28} className="text-slate-600" />
            </div>
            <p className="text-slate-500 text-sm">暂无导入记录</p>
            <p className="text-slate-600 text-xs mt-1">上传 Excel 文件开始导入</p>
          </div>
        ) : null}
      </div>

      <BottomNav />
    </div>
  )
}
