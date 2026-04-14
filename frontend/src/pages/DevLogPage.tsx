import { useState, useEffect } from 'react'
import { Search, Clock, GitCommit, FileText, Loader2, ChevronRight } from 'lucide-react'
import { fetchDevLogs, fetchDevLogStats, type DevLogEntry, type DevLogStats } from '../api/devlog'
import BottomNav from '../components/BottomNav'

const TYPE_ICONS: Record<string, typeof GitCommit> = {
  feature: GitCommit,
  bugfix: FileText,
  refactor: FileText,
  change: FileText,
}

const SOURCE_LABELS: Record<string, string> = {
  file: '文件变更',
  session: '对话摘要',
  git: 'Git 提交',
  agent: 'Agent',
}

function formatTime(ts: number): string {
  const d = new Date(ts * 1000)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffDays === 0) {
    const h = Math.floor(diffMs / 3600000)
    if (h === 0) {
      const m = Math.floor(diffMs / 60000)
      return m <= 1 ? '刚刚' : `${m} 分钟前`
    }
    return `${h} 小时前`
  }
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function qualityColor(q: number): string {
  if (q >= 70) return 'text-green-400'
  if (q >= 40) return 'text-amber-400'
  return 'text-slate-400'
}

export default function DevLogPage() {
  const [query, setQuery] = useState('')
  const [entries, setEntries] = useState<DevLogEntry[]>([])
  const [stats, setStats] = useState<DevLogStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await fetchDevLogStats()
      setStats(data)
    } catch (e) {
      console.error('Failed to load stats:', e)
    }
  }

  const doSearch = async (searchQuery: string) => {
    setSearching(true)
    setError('')
    setHasSearched(true)
    try {
      const data = await fetchDevLogs({
        q: searchQuery || undefined,
        type: typeFilter || undefined,
        source: sourceFilter || undefined,
        limit: 50,
      })
      setEntries(data.entries)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '搜索失败')
      setEntries([])
    } finally {
      setSearching(false)
    }
  }

  const handleSearch = () => doSearch(query)

  useEffect(() => {
    if (!hasSearched) return
    doSearch(query)
  }, [typeFilter, sourceFilter])

  const handleRefresh = () => {
    loadStats()
    if (hasSearched) doSearch(query)
  }

  // Initial load
  useEffect(() => {
    setLoading(true)
    doSearch('').finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-white text-xl font-bold">开发日志</h1>
          <button
            onClick={handleRefresh}
            className="text-slate-400 hover:text-white text-xs flex items-center gap-1"
          >
            <Loader2 size={12} className={loading ? 'animate-spin' : ''} />
            刷新
          </button>
        </div>

        {/* Search */}
        <div className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="搜索日志内容..."
              className="w-full bg-slate-800 text-white text-sm rounded-xl pl-9 pr-4 py-2.5 placeholder-slate-500 border border-slate-700 focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white rounded-xl px-4 py-2.5 text-sm"
          >
            {searching ? <Loader2 size={16} className="animate-spin" /> : '搜索'}
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <select
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="bg-slate-800 text-white text-xs rounded-lg px-2 py-1.5 border border-slate-700"
          >
            <option value="">全部类型</option>
            <option value="feature">feature</option>
            <option value="bugfix">bugfix</option>
            <option value="refactor">refactor</option>
            <option value="change">change</option>
          </select>
          <select
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
            className="bg-slate-800 text-white text-xs rounded-lg px-2 py-1.5 border border-slate-700"
          >
            <option value="">全部来源</option>
            <option value="file">文件变更</option>
            <option value="session">对话摘要</option>
            <option value="git">Git 提交</option>
            <option value="agent">Agent</option>
          </select>
        </div>

        {/* Stats */}
        {stats && (
          <div className="flex gap-4 mt-3">
            <span className="text-slate-500 text-xs">共 {stats.total} 条</span>
            {Object.entries(stats.by_type).map(([t, c]) => (
              <span key={t} className="text-slate-500 text-xs">
                {t}: {c}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 text-red-400 text-sm">{error}</div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 size={24} className="animate-spin text-slate-500" />
        </div>
      )}

      {/* Entries */}
      {!loading && entries.length > 0 && (
        <div className="px-4 space-y-2">
          {entries.map(entry => {
            const Icon = TYPE_ICONS[entry.type] || FileText
            const isExpanded = expandedId === entry.id
            return (
              <div
                key={entry.id}
                className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden"
              >
                <button
                  className="w-full text-left p-4"
                  onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                >
                  <div className="flex items-start gap-3">
                    <Icon size={16} className="text-blue-400 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-medium ${qualityColor(entry.quality)}`}>
                          q:{entry.quality}
                        </span>
                        <span className="text-slate-500 text-xs">·</span>
                        <span className="text-slate-500 text-xs">
                          {SOURCE_LABELS[entry.source] || entry.source}
                        </span>
                        <span className="text-slate-500 text-xs">·</span>
                        <span className="text-slate-500 text-xs flex items-center gap-1">
                          <Clock size={10} />
                          {formatTime(entry.created_at)}
                        </span>
                      </div>
                      <div className="text-white text-sm font-medium leading-snug">
                        {entry.title}
                      </div>
                      {entry.file_path && (
                        <div className="text-slate-500 text-xs mt-1 truncate">
                          {entry.file_path}
                        </div>
                      )}
                    </div>
                    <ChevronRight
                      size={16}
                      className={`text-slate-600 shrink-0 mt-1 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                    />
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t border-slate-700">
                    <div className="text-slate-300 text-xs leading-relaxed whitespace-pre-wrap break-all">
                      {entry.content}
                    </div>
                    {entry.tags.length > 0 && (
                      <div className="flex gap-1 mt-2 flex-wrap">
                        {entry.tags.map(tag => (
                          <span
                            key={tag}
                            className="bg-slate-700 text-slate-400 text-xs px-2 py-0.5 rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Empty state */}
      {!loading && entries.length === 0 && !error && (
        <div className="px-4 pt-8 text-center">
          <div className="text-slate-500 text-sm">
            {hasSearched ? '没有找到匹配的日志' : '暂无开发日志'}
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  )
}
