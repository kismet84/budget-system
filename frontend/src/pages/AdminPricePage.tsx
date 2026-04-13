import { useState, useRef, useCallback } from 'react'
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle, Loader2, BarChart3 } from 'lucide-react'
import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 60000,
})

interface ImportReport {
  total_rows: number
  imported: number
  skipped: number
  errors: string[]
  filename: string
  month: string
}

interface HistoryReport {
  total_rows: number
  imported: number
  skipped: number
  errors: string[]
  filename: string
  month: string
  region?: string
}

export default function AdminPricePage() {
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [report, setReport] = useState<ImportReport | null>(null)
  const [history, setHistory] = useState<HistoryReport[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [priceType, setPriceType] = useState('信息价')
  const [selectedRegion, setSelectedRegion] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true)
    try {
      const res = await api.get<HistoryReport[]>('/api/v1/admin/price/report')
      setHistory(res.data)
    } catch (err) {
      console.error('Failed to fetch history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }, [])

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('仅支持 .xlsx 或 .xls 格式')
      return
    }

    setUploading(true)
    setReport(null)

    const formData = new FormData()
    formData.append('file', file)
    if (selectedRegion) {
      formData.append('region', selectedRegion)
    }
    formData.append('price_type', priceType)

    try {
      const res = await api.post<ImportReport>('/api/v1/admin/price/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setReport(res.data)
    } catch (err: any) {
      const msg = err.response?.data?.detail || '导入失败，请检查文件格式'
      setReport({
        total_rows: 0,
        imported: 0,
        skipped: 0,
        errors: [msg],
        filename: file.name,
        month: '未知',
      })
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => setDragOver(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleViewHistory = () => {
    fetchHistory()
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BarChart3 size={20} className="text-blue-400" />
            <h1 className="text-white text-xl font-bold">信息价导入</h1>
          </div>
          <button
            onClick={handleViewHistory}
            className="text-slate-400 hover:text-white text-sm flex items-center gap-1"
          >
            查看导入历史
          </button>
        </div>

        {/* Options */}
        <div className="flex gap-3 mb-4">
          <select
            value={priceType}
            onChange={(e) => setPriceType(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="信息价">信息价</option>
            <option value="企业价">企业价</option>
          </select>
          <input
            type="text"
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            placeholder="指定地区（可选，留空则自动识别）"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
            ${dragOver
              ? 'border-blue-400 bg-blue-900/20'
              : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            className="hidden"
            onChange={handleInputChange}
          />
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <Loader2 size={32} className="animate-spin text-blue-400" />
              <p className="text-slate-400 text-sm">正在解析并导入...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-blue-900/50 flex items-center justify-center">
                <Upload size={24} className="text-blue-400" />
              </div>
              <div>
                <p className="text-white font-medium">点击或拖拽上传 Excel 文件</p>
                <p className="text-slate-500 text-xs mt-1">支持 .xlsx / .xls 格式</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-4 space-y-6">
        {/* Report */}
        {report && (
          <div className="bg-slate-800 rounded-xl p-4">
            <h2 className="text-white font-medium mb-4 flex items-center gap-2">
              <FileSpreadsheet size={18} className="text-blue-400" />
              导入报告
            </h2>

            {/* Summary */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-blue-400">{report.total_rows}</p>
                <p className="text-slate-400 text-xs">解析行数</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-400">{report.imported}</p>
                <p className="text-slate-400 text-xs">成功导入</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-yellow-400">{report.skipped}</p>
                <p className="text-slate-400 text-xs">跳过</p>
              </div>
            </div>

            {/* File Info */}
            <div className="bg-slate-700/30 rounded-lg p-3 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">文件名</span>
                <span className="text-white">{report.filename}</span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-slate-400">月份</span>
                <span className="text-white">{report.month}</span>
              </div>
            </div>

            {/* Status */}
            {report.imported > 0 ? (
              <div className="flex items-center gap-2 text-green-400 bg-green-900/20 rounded-lg p-3">
                <CheckCircle size={18} />
                <span className="text-sm">导入成功，共 {report.imported} 条记录</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-400 bg-red-900/20 rounded-lg p-3">
                <AlertCircle size={18} />
                <span className="text-sm">导入失败，请检查文件格式</span>
              </div>
            )}

            {/* Errors */}
            {report.errors.length > 0 && (
              <div className="mt-4">
                <p className="text-slate-400 text-xs mb-2">错误信息：</p>
                <div className="bg-red-900/20 rounded-lg p-3 max-h-40 overflow-y-auto">
                  {report.errors.map((err, i) => (
                    <p key={i} className="text-red-300 text-xs">{err}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div className="bg-slate-800 rounded-xl p-4">
            <h2 className="text-white font-medium mb-4">导入历史</h2>
            <div className="space-y-3">
              {history.map((h, i) => (
                <div key={i} className="bg-slate-700/50 rounded-lg p-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-white text-sm font-medium">{h.filename}</p>
                      <p className="text-slate-400 text-xs mt-1">{h.month} · {h.region || '多地区'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-green-400 text-sm">{h.imported} 条</p>
                      <p className="text-slate-500 text-xs">{h.total_rows} 解析</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {loadingHistory && (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={24} className="animate-spin text-slate-400" />
          </div>
        )}

        {/* Format Guide */}
        <div className="bg-slate-800 rounded-xl p-4">
          <h2 className="text-white font-medium mb-3">Excel 格式说明</h2>
          <div className="text-slate-400 text-sm space-y-2">
            <p>• 文件需为标准 Excel 格式（.xlsx）</p>
            <p>• 数据从第 6 行开始（第 1-5 行为表头）</p>
            <p>• 必需列：序号(A)、编号(B)、名称(C)、规格(D)、单位(E)</p>
            <p>• 价格列：含税价/除税价，需为正数</p>
            <p>• 支持湖北省各地市信息价自动识别</p>
            <p>• 自动从文件名提取月份（如 "2025年8月"）</p>
          </div>
        </div>
      </div>
    </div>
  )
}
