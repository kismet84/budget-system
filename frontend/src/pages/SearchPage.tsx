import { useState, useEffect } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { searchQuotas } from '../api/quota'
import QuotaCard from '../components/QuotaCard'
import BottomNav from '../components/BottomNav'
import type { QuotaResult } from '../types/quota'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [count, setCount] = useState(3)
  const [matchLevel, setMatchLevel] = useState('中匹配以上')
  const [sectionFilter, setSectionFilter] = useState('')
  const [sections, setSections] = useState<{value: string; label: string}[]>([])
  const [results, setResults] = useState<QuotaResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 页面加载时获取所有分部
  useEffect(() => {
    fetch('/api/v1/quota/sections')
      .then(r => r.json())
      .then(data => setSections(data))
      .catch(() => {})
  }, [])

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    try {
      const data = await searchQuotas(query.trim(), count, sectionFilter || undefined)
      const all = data?.results ?? []

      // 按匹配度过滤
      const threshold = matchLevel === '高匹配' ? 0.9 : matchLevel === '中匹配以上' ? 0.7 : 0
      const filtered = all.filter(r => (r.similarity ?? 0) >= threshold)

      setResults(filtered)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '搜索失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 z-10 px-4 pt-6 pb-4">
        <h1 className="text-white text-xl font-bold mb-4">定额搜索</h1>

        {/* Search Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="输入施工内容，如：内墙抹灰 20mm厚"
            className="flex-1 bg-slate-800 text-white text-sm rounded-xl px-4 py-3 placeholder-slate-500 border border-slate-700 focus:border-blue-500"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl px-5 py-3 flex items-center gap-2 text-sm font-medium transition-colors"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-4 mt-3">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-xs">条目</span>
            <select
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="bg-slate-800 text-white text-xs rounded-lg px-2 py-1 border border-slate-700"
            >
              <option value={3}>3条</option>
              <option value={5}>5条</option>
              <option value={10}>10条</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-xs">匹配度</span>
            <select
              value={matchLevel}
              onChange={(e) => setMatchLevel(e.target.value)}
              className="bg-slate-800 text-white text-xs rounded-lg px-2 py-1 border border-slate-700"
            >
              <option value="低匹配以上">低匹配以上</option>
              <option value="中匹配以上">中匹配以上</option>
              <option value="高匹配">高匹配</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-xs">分部</span>
            <select
              value={sectionFilter}
              onChange={(e) => setSectionFilter(e.target.value)}
              className="bg-slate-800 text-white text-xs rounded-lg px-2 py-1 border border-slate-700"
            >
              <option value="">全部</option>
              {sections.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-8 text-slate-400 text-sm">
            正在搜索…
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-3 text-red-400 text-sm text-center">{error}</div>
        )}
      </div>

      {/* Results */}
      {!loading && results.length > 0 && (
        <div className="px-4 space-y-3">
          <div className="text-slate-400 text-xs px-1">
            找到 {results.length} 条相关定额
          </div>
          {results.map((quota, i) => (
            <QuotaCard
              key={quota.quota_id}
              quota={quota}
              rank={i}
              cachedResults={results}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && results.length === 0 && !error && (
        <div className="px-4 pt-8 text-center">
          <div className="text-slate-500 text-sm">
            输入施工描述，开始搜索定额
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  )
}
